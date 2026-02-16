"""Comprehensive error handler for Discord commands and client events."""

import importlib
import sys
import traceback
from typing import Any

import discord
import sentry_sdk
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.services.sentry import (
    capture_exception_safe,
    set_command_context,
    set_user_context,
    track_command_end,
)
from tux.services.sentry import (
    is_initialized as sentry_is_initialized,
)

from .config import ERROR_CONFIG_MAP, ErrorHandlerConfig
from .extractors import unwrap_error
from .formatter import ErrorFormatter
from .suggestions import CommandSuggester


class ErrorHandler(commands.Cog):
    """Centralized error handling for commands and client events.

    Handles app command (tree.on_error), prefix/hybrid (on_command_error), and
    raw client events (Client.on_error for on_ready, on_member_join, etc.).
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the error handler cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        self.bot = bot
        self.formatter = ErrorFormatter()
        self.suggester = CommandSuggester()
        self._old_tree_error: Any = None
        self._old_client_on_error: Any = None

    async def cog_load(self) -> None:
        """Override app command and client event error handlers."""
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

        self._old_client_on_error = self.bot.on_error
        self.bot.on_error = self._on_client_error

        logger.debug("Error handler loaded")

    async def cog_unload(self) -> None:
        """Restore original app command and client error handlers."""
        if self._old_tree_error is not None:
            self.bot.tree.on_error = self._old_tree_error
        if self._old_client_on_error is not None:
            self.bot.on_error = self._old_client_on_error
        logger.debug("Error handler unloaded")

    async def cog_reload(self) -> None:
        """Handle cog reload - force reload imported modules."""
        # Force reload the config and extractors modules
        modules_to_reload = [
            "tux.services.handlers.error.config",
            "tux.services.handlers.error.extractors",
            "tux.services.handlers.error.formatter",
            "tux.services.handlers.error.suggestions",
        ]

        for module_name in modules_to_reload:
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    logger.debug(f"Force reloaded {module_name}")
                except Exception as e:
                    # Module reloading can fail for various reasons (ImportError, AttributeError, etc.)
                    # Catching Exception is appropriate here as we want to continue reloading other modules
                    logger.warning(f"Failed to reload {module_name}: {e}")

        logger.debug("Error handler reloaded with fresh modules")

    async def _on_client_error(
        self,
        event_method: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Handle errors in non-command event listeners (e.g. on_ready, on_member_join).

        When an event listener raises, discord.py calls Client.on_error. We override
        that here to log full tracebacks and report to Sentry, replacing the default
        'Ignoring exception in {event}' with actionable diagnostics. The exception
        is not passed by discord; we use sys.exception() (or sys.exc_info()).
        """
        exc = sys.exception()
        if exc is not None and isinstance(exc, Exception):
            logger.exception("Exception in event %s: %s", event_method, exc)
            capture_exception_safe(exc, extra_context={"event": event_method})
        else:
            logger.error(
                "Exception in event %s (exception context not available)",
                event_method,
            )

    async def _handle_error(
        self,
        source: commands.Context[Tux] | discord.Interaction,
        error: Exception,
    ) -> None:
        """Handle errors for commands and interactions."""
        # Unwrap nested errors
        root_error = unwrap_error(error)

        # Get error configuration
        config = self._get_error_config(root_error)

        # Set Sentry context when we will report to Sentry
        if config.send_to_sentry:
            self._set_sentry_context(source, root_error)

        # Log error (includes action summary)
        self._log_error(root_error, config, source)

        # Send embed first so the user sees a response immediately
        sent_message: discord.Message | None = None
        if config.send_embed:
            embed = self.formatter.format_error_embed(root_error, source, config)
            sent_message = await self._send_error_response(
                source,
                embed,
                wait_for_message=config.send_to_sentry,
            )

        # Capture to Sentry and get event_id (avoid double-capture: only fallback when not initialized)
        event_id: str | None = None
        if config.send_to_sentry and sentry_is_initialized():
            try:
                event_id = sentry_sdk.capture_exception(root_error)
            except Exception as capture_error:
                logger.warning(
                    "Failed to capture exception to Sentry: %s",
                    capture_error,
                )
                capture_exception_safe(root_error)
        elif config.send_to_sentry:
            capture_exception_safe(root_error)

        # Edit the sent message to add Sentry error ID in footer when applicable
        if config.send_embed and event_id and sent_message is not None:
            try:
                updated_embed = self.formatter.format_error_embed(
                    root_error,
                    source,
                    config,
                    event_id=event_id,
                )
                await sent_message.edit(embed=updated_embed)
            except discord.HTTPException as e:
                logger.debug("Could not edit error message with event_id: %s", e)
        elif config.send_embed and event_id and isinstance(source, discord.Interaction):
            # We used response.send_message (no message ref); edit original response
            try:
                updated_embed = self.formatter.format_error_embed(
                    root_error,
                    source,
                    config,
                    event_id=event_id,
                )
                await source.edit_original_response(embed=updated_embed)
            except discord.HTTPException as e:
                logger.debug("Could not edit original response with event_id: %s", e)

    def _set_sentry_context(
        self,
        source: commands.Context[Tux] | discord.Interaction,
        error: Exception,
    ) -> None:
        """Set enhanced Sentry context for error reporting."""
        # Set command context (includes Discord info, performance data, etc.)
        set_command_context(source)

        # Set user context (includes permissions, roles, etc.)
        if isinstance(source, discord.Interaction):
            set_user_context(source.user)
        else:
            set_user_context(source.author)

        # Track command failure for performance metrics
        command_name = None
        command_name = source.command.qualified_name if source.command else "unknown"
        if command_name and command_name != "unknown":
            track_command_end(command_name, success=False, error=error)

    def _get_error_config(self, error: Exception) -> ErrorHandlerConfig:
        """Get configuration for error type.

        Returns
        -------
        ErrorHandlerConfig
            Configuration for the error type.
        """
        error_type = type(error)

        # Check exact match
        if error_type in ERROR_CONFIG_MAP:
            return ERROR_CONFIG_MAP[error_type]

        # Check parent classes
        for base_type in error_type.__mro__:
            if base_type in ERROR_CONFIG_MAP:
                return ERROR_CONFIG_MAP[base_type]

        # Default config
        return ErrorHandlerConfig()

    def _log_error(
        self,
        error: Exception,
        config: ErrorHandlerConfig,
        source: commands.Context[Tux] | discord.Interaction,
    ) -> None:
        """Log error with appropriate level and context.

        Parameters
        ----------
        error : Exception
            The error to log.
        config : ErrorHandlerConfig
            Configuration for error handling.
        source : commands.Context[Tux] | discord.Interaction
            The command context or interaction that triggered the error.
        """
        # Use logger.error as safe fallback if log_level is invalid
        log_func = getattr(logger, config.log_level.lower(), logger.error)
        error_type = type(error).__name__
        error_msg = str(error)

        # Extract command and guild context for better diagnosability
        command_name = source.command.qualified_name if source.command else "unknown"
        guild_id = source.guild.id if source.guild else "unknown"
        source_type = (
            "interaction" if isinstance(source, discord.Interaction) else "command"
        )
        context = f" ({source_type}={command_name}, guild_id={guild_id})"

        if config.send_to_sentry:
            # Include traceback for errors going to Sentry
            tb = "".join(
                traceback.format_exception(type(error), error, error.__traceback__),
            )
            log_func(
                f"Encountered error [{error_type}]{context}: {error_msg}\n"
                f"Traceback:\n{tb}",
            )
        else:
            # Build action summary
            actions: list[str] = []
            if config.send_embed:
                actions.append("sending to user")
            actions.append("not sent to Sentry")
            action_summary = f" ({', '.join(actions)})" if actions else ""

            log_func(
                f"Encountered error [{error_type}]{context}{action_summary}: {error_msg}",
            )

    async def _send_error_response(
        self,
        source: commands.Context[Tux] | discord.Interaction,
        embed: discord.Embed,
        *,
        wait_for_message: bool = False,
    ) -> discord.Message | None:
        """Send error response to user.

        When wait_for_message is True, returns the sent message so the caller can
        edit it later (e.g. to add Sentry event_id). For interaction.response.send_message
        we cannot get the message; caller must use edit_original_response.
        """
        try:
            if isinstance(source, discord.Interaction):
                if source.response.is_done():
                    return await source.followup.send(
                        embed=embed,
                        ephemeral=True,
                        wait=wait_for_message,
                    )
                await source.response.send_message(embed=embed, ephemeral=True)
                return None
            # Prefix command
            return await source.reply(embed=embed, mention_author=False)
        except discord.HTTPException as e:
            logger.warning(f"Failed to send error response: {e}")
            return None
        except Exception as e:
            logger.exception("Unexpected error while sending error response: {}", e)
            return None

    @commands.Cog.listener("on_command_error")
    async def on_command_error(
        self,
        ctx: commands.Context[Tux],
        error: commands.CommandError,
    ) -> None:
        """Handle prefix command errors."""
        # Handle CommandNotFound with suggestions
        if isinstance(error, commands.CommandNotFound):
            config = self._get_error_config(error)
            if config.suggest_similar_commands:
                await self.suggester.handle_command_not_found(ctx)
            return

        # Skip if command has local error handler
        if ctx.command and ctx.command.has_error_handler():
            return

        # Skip if cog has local error handler (except this cog)
        if ctx.cog and ctx.cog.has_error_handler() and ctx.cog is not self:
            return

        await self._handle_error(ctx, error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction[Tux],
        error: app_commands.AppCommandError,
    ) -> None:
        """Handle app command errors."""
        await self._handle_error(interaction, error)


async def setup(bot: Tux) -> None:
    """Cog setup for error handler.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(ErrorHandler(bot))
