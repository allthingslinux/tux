from typing import Any, ClassVar

import discord
import sentry_sdk
from discord.ext import commands
from loguru import logger

from tux.core.types import Tux
from tux.services.tracing import capture_span_exception, set_span_attributes, set_span_status

# Type alias using PEP695 syntax
type CommandObject = (
    commands.Command[Any, ..., Any] | discord.app_commands.Command[Any, ..., Any] | discord.app_commands.ContextMenu
)


class SentryHandler(commands.Cog):
    """
    Handles Sentry error tracking and status management for commands and interactions.

    This cog works with the automatic instrumentation from tracing.py to provide
    proper error handling and status management for both prefix commands and slash commands.
    It does not create transactions manually, as that is handled by the automatic
    instrumentation system.
    """

    # Standard Sentry transaction statuses with ClassVar
    # See: https://develop.sentry.dev/sdk/event-payloads/transaction/#transaction-status
    STATUS: ClassVar[dict[str, str]] = {
        "OK": "ok",
        "UNKNOWN": "unknown",
        "ERROR": "internal_error",
        "NOT_FOUND": "not_found",
        "PERMISSION_DENIED": "permission_denied",
        "INVALID_ARGUMENT": "invalid_argument",
        "RESOURCE_EXHAUSTED": "resource_exhausted",
        "UNAUTHENTICATED": "unauthenticated",
        "CANCELLED": "cancelled",
    }

    def __init__(self, bot: Tux) -> None:
        """Initialize the Sentry handler cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach the listeners to
        """
        self.bot = bot
        logger.info("Sentry handler initialized")

    def _is_sentry_available(self) -> bool:
        """Check if Sentry is initialized and available for use.

        Returns
        -------
        bool
            True if Sentry is initialized, False otherwise
        """
        return sentry_sdk.is_initialized()

    def _set_command_context(self, ctx: commands.Context[Tux] | discord.Interaction, command_name: str) -> None:
        """Set command context on the current Sentry span.

        Parameters
        ----------
        ctx : Union[commands.Context[Tux], discord.Interaction]
            The command context or interaction
        command_name : str
            The name of the command being executed
        """
        if not self._is_sentry_available():
            return

        # Set command-specific span attributes for tracing
        if isinstance(ctx, commands.Context):
            set_span_attributes(
                {
                    "discord.command.name": command_name,
                    "discord.guild.id": str(ctx.guild.id) if ctx.guild else "DM",
                    "discord.channel.id": ctx.channel.id,
                    "discord.user.id": ctx.author.id,
                    "discord.message.id": ctx.message.id,
                    "discord.command.type": "prefix",
                },
            )
        else:  # discord.Interaction
            set_span_attributes(
                {
                    "discord.command.name": command_name,
                    "discord.guild.id": str(ctx.guild_id) if ctx.guild_id else "DM",
                    "discord.channel.id": ctx.channel_id,
                    "discord.user.id": ctx.user.id,
                    "discord.interaction.id": ctx.id,
                    "discord.interaction.type": ctx.type.name,
                    "discord.command.type": "slash",
                },
            )

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context[Tux]) -> None:
        """
        Set context for a prefix command execution.

        This works with the automatic instrumentation to add command-specific
        context to the existing transaction.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        """
        if command_name := (ctx.command.qualified_name if ctx.command else "Unknown Command"):
            self._set_command_context(ctx, command_name)
            logger.trace(f"Set context for prefix command: {command_name}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context[Tux], error: commands.CommandError) -> None:
        """
        Handle errors for prefix commands.

        This captures command errors and sets the appropriate status on the
        current transaction.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        error : commands.CommandError
            The error that occurred
        """
        if not self._is_sentry_available():
            return

        # Capture the error in the current span
        capture_span_exception(error, command_name=ctx.command.qualified_name if ctx.command else "Unknown")

        # Set appropriate status based on error type
        if isinstance(error, commands.CommandNotFound):
            set_span_status("NOT_FOUND")
        elif isinstance(error, commands.MissingPermissions):
            set_span_status("PERMISSION_DENIED")
        elif isinstance(error, commands.BadArgument):
            set_span_status("INVALID_ARGUMENT")
        else:
            set_span_status("ERROR")

        logger.debug(f"Captured error for prefix command: {error}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """
        Set context for application command interactions.

        This works with the automatic instrumentation to add command-specific
        context to the existing transaction.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object
        """
        if interaction.type != discord.InteractionType.application_command:
            return

        if command_name := (interaction.command.qualified_name if interaction.command else "Unknown App Command"):
            self._set_command_context(interaction, command_name)
            logger.trace(f"Set context for app command: {command_name}")

    @commands.Cog.listener()
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """
        Handle errors for application commands.

        This captures command errors and sets the appropriate status on the
        current transaction.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object
        error : discord.app_commands.AppCommandError
            The error that occurred
        """
        if not self._is_sentry_available():
            return

        # Capture the error in the current span
        command_name = interaction.command.qualified_name if interaction.command else "Unknown"
        capture_span_exception(error, command_name=command_name)

        # Set appropriate status based on error type
        if isinstance(error, discord.app_commands.CommandNotFound):
            set_span_status("NOT_FOUND")
        elif isinstance(error, discord.app_commands.MissingPermissions):
            set_span_status("PERMISSION_DENIED")
        else:
            set_span_status("ERROR")

        logger.debug(f"Captured error for app command: {error}")


async def setup(bot: Tux) -> None:
    """Add the SentryHandler cog to the bot."""
    await bot.add_cog(SentryHandler(bot))
