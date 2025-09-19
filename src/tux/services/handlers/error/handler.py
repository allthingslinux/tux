"""Main error handler implementation."""

import traceback
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.services.sentry_manager import SentryManager

from .config import ErrorHandlerConfig
from .extractors import unwrap_error
from .formatter import ErrorFormatter
from .suggestions import CommandSuggester

# Type alias for contexts and interactions
ContextOrInteraction = commands.Context[Tux] | discord.Interaction[Tux]


class ErrorHandler(commands.Cog):
    """
    Centralized error handling for both traditional (prefix) and application (slash) commands.

    This cog intercepts errors from command execution and provides user-friendly
    error messages while logging technical details for debugging. It handles both
    expected errors (like permission issues) and unexpected errors (like bugs).
    """

    def __init__(self, bot: Tux, config: ErrorHandlerConfig | None = None) -> None:
        """
        Initialize the ErrorHandler.

        Args:
            bot: The bot instance.
            config: Optional configuration for error handling behavior.
        """
        self.bot = bot
        self.config = config or ErrorHandlerConfig()
        self.formatter = ErrorFormatter()
        self.suggester = CommandSuggester(self.config.suggestion_delete_after)

        # Store the original app command error handler so we can restore it later
        self._old_tree_error: Any = None

    async def cog_load(self) -> None:
        """
        Overrides the bot's application command tree error handler when the cog is loaded.

        This ensures that application command errors are routed through our
        centralized error handling system.
        """
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

        logger.debug("Application command error handler mapped.")

    async def cog_unload(self) -> None:
        """
        Restores the original application command tree error handler when the cog is unloaded.

        This cleanup ensures that we don't leave dangling references when the
        cog is reloaded or the bot is shut down.
        """
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

        logger.debug("Application command error handler restored.")

    # --- Core Error Processing Logic ---

    async def _handle_error(self, source: ContextOrInteraction, error: Exception) -> None:
        """
        The main internal method for processing any intercepted command error.

        This method:
        1. Unwraps nested exceptions to find the root cause
        2. Determines if the error should be logged to Sentry
        3. Formats a user-friendly error message
        4. Sends the error response to the user
        5. Logs the error with appropriate detail level

        Args:
            source: The context or interaction where the error occurred.
            error: The exception that was raised.
        """
        # Unwrap nested exceptions to get the actual error
        unwrapped_error = unwrap_error(error)

        # Get command signature for context
        command_signature = self._get_command_signature(source)

        # Create user-friendly error embed
        embed = self.formatter.format_error_embed(unwrapped_error, command_signature)

        # Send error response to user
        sent_message = await self._send_error_response(source, embed)

        # Log error and potentially report to Sentry
        sentry_event_id = await self._log_and_report_error(source, unwrapped_error)

        # Try to edit the message with Sentry ID if available
        if sentry_event_id and sent_message:
            await self._try_edit_message_with_sentry_id(sent_message, sentry_event_id)

    def _get_context_command_signature(self, ctx: commands.Context[Tux]) -> str | None:
        """Get the command signature for a traditional command context."""
        command = ctx.command
        if command is None:
            return None

        # Build signature with prefix and parameters
        signature = command.signature
        prefix = ctx.prefix
        qualified_name = command.qualified_name
        return f"{prefix}{qualified_name}{f' {signature}' if signature else ''}"

    def _get_command_signature(self, source: ContextOrInteraction) -> str | None:
        """Get the command signature for display in error messages."""
        if isinstance(source, commands.Context):
            return self._get_context_command_signature(source)

        # Must be an interaction if not a context
        # For app commands, we need to reconstruct the signature
        if source.command is None:
            return None

        command_name = source.command.qualified_name
        return f"/{command_name}"

    async def _send_error_response(self, source: ContextOrInteraction, embed: discord.Embed) -> discord.Message | None:
        """
        Sends the generated error embed to the user via the appropriate channel/method.

        Args:
            source: The context or interaction where the error occurred.
            embed: The error embed to send.

        Returns:
            The sent message, or None if sending failed.
        """
        try:
            if isinstance(source, commands.Context):
                # For traditional commands, send a regular message
                if self.config.delete_error_messages:
                    delete_after = float(self.config.error_message_delete_after)
                    return await source.send(embed=embed, delete_after=delete_after)
                return await source.send(embed=embed)

            # Must be an interaction if not a context
            # For application commands, we need to handle response vs followup
            if source.response.is_done():
                # Response already sent, use followup
                return await source.followup.send(embed=embed, ephemeral=True)
            # Send initial response
            await source.response.send_message(embed=embed, ephemeral=True)
            return await source.original_response()

        except discord.HTTPException as e:
            logger.warning(f"Failed to send error response: {e}")
            return None

    async def _log_and_report_error(self, source: ContextOrInteraction, error: Exception) -> str | None:
        """
        Logs the error and reports it to Sentry if appropriate.

        Args:
            source: The context or interaction where the error occurred.
            error: The exception that occurred.

        Returns:
            Sentry event ID if the error was reported, None otherwise.
        """
        # Determine if this is an expected error that shouldn't be reported to Sentry
        expected_errors = (
            commands.CommandNotFound,
            commands.MissingPermissions,
            commands.BotMissingPermissions,
            commands.MissingRole,
            commands.BotMissingRole,
            commands.MissingAnyRole,
            commands.BotMissingAnyRole,
            commands.NotOwner,
            commands.MissingRequiredArgument,
            commands.BadArgument,
            commands.CommandOnCooldown,
            commands.MaxConcurrencyReached,
            commands.DisabledCommand,
            commands.CheckFailure,
            commands.CheckAnyFailure,
        )

        # Log the error with appropriate level
        if isinstance(error, expected_errors):
            logger.info(f"Expected error in command: {error}")
            return None

        logger.error(f"Unexpected error in command: {error}")
        logger.error(f"Traceback: {''.join(traceback.format_exception(type(error), error, error.__traceback__))}")

        # Report to Sentry for unexpected errors
        sentry_manager = SentryManager()

        # Get user ID safely - Context has author, Interaction has user
        if isinstance(source, commands.Context):
            author = source.author
            user_id = author.id
        else:
            # Must be an interaction if not a context
            user = source.user
            user_id = user.id if user else None

        # Get channel ID safely - both Context and Interaction have channel
        channel = source.channel
        channel_id = channel.id if channel else None

        # Get guild ID safely
        guild = source.guild
        guild_id = guild.id if guild else None

        return sentry_manager.capture_exception(
            error,
            level="error",
            context={
                "command": self._get_command_signature(source),
                "user_id": user_id,
                "guild_id": guild_id,
                "channel_id": channel_id,
            },
        )

    async def _try_edit_message_with_sentry_id(
        self,
        sent_message: discord.Message | None,
        sentry_event_id: str,
    ) -> None:
        """
        Attempts to edit the error message to include the Sentry event ID.

        Args:
            sent_message: The message that was sent with the error.
            sentry_event_id: The Sentry event ID to include.
        """
        if not sent_message or not sentry_event_id:
            return

        try:
            # Get the current embed and add the Sentry ID
            if embeds := sent_message.embeds:
                embed = embeds[0]
                embed.set_footer(text=f"Error ID: {sentry_event_id}")
                await sent_message.edit(embed=embed)
        except discord.HTTPException:
            # If editing fails, just log it - not critical
            logger.debug(f"Failed to edit message with Sentry ID: {sentry_event_id}")

    # --- Event Listeners ---

    @commands.Cog.listener("on_command_error")
    async def on_command_error_listener(self, ctx: commands.Context[Tux], error: commands.CommandError) -> None:
        """
        The primary listener for errors occurring in traditional (prefix) commands.

        This method is automatically called by discord.py when a command error
        occurs. It serves as the entry point for our centralized error handling.

        Args:
            ctx: The context in which the error occurred.
            error: The command error that was raised.
        """
        # Special handling for CommandNotFound if suggestions are enabled
        if isinstance(error, commands.CommandNotFound) and self.config.suggest_similar_commands:
            await self.suggester.handle_command_not_found(ctx)
            return

        # Handle all other errors through the main error handler
        await self._handle_error(ctx, error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction[Tux],
        error: app_commands.AppCommandError,
    ) -> None:
        """
        The primary handler for errors occurring in application (slash) commands.

        This method is set as the bot's tree error handler during cog loading.
        It processes application command errors and routes them through our
        centralized error handling system.

        Args:
            interaction: The interaction that caused the error.
            error: The application command error that was raised.
        """
        # Handle the error through our main error handler
        await self._handle_error(interaction, error)
