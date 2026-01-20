"""Comprehensive error handler for Discord commands and client events."""

import importlib
import sys
import traceback
from typing import Any

import discord
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

        # Set Sentry context for enhanced error reporting
        if config.send_to_sentry:
            self._set_sentry_context(source, root_error)

        # Log error
        self._log_error(root_error, config)

        # Send user response if configured
        if config.send_embed:
            embed = self.formatter.format_error_embed(root_error, source, config)
            await self._send_error_response(source, embed)

        # Report to Sentry if configured
        if config.send_to_sentry:
            capture_exception_safe(root_error)

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

    def _log_error(self, error: Exception, config: ErrorHandlerConfig) -> None:
        """Log error with appropriate level."""
        log_func = getattr(logger, config.log_level.lower())

        if config.send_to_sentry:
            # Include traceback for errors going to Sentry
            tb = "".join(
                traceback.format_exception(type(error), error, error.__traceback__),
            )
            log_func(f"Error: {error}\nTraceback:\n{tb}")
        else:
            log_func(f"Error (not sent to Sentry): {error}")

    async def _send_error_response(
        self,
        source: commands.Context[Tux] | discord.Interaction,
        embed: discord.Embed,
    ) -> None:
        """Send error response to user."""
        try:
            if isinstance(source, discord.Interaction):
                # App command - ephemeral response
                if source.response.is_done():
                    await source.followup.send(embed=embed, ephemeral=True)
                else:
                    await source.response.send_message(embed=embed, ephemeral=True)
            # Prefix command
            else:
                await source.reply(embed=embed, mention_author=False)
        except discord.HTTPException as e:
            logger.warning(f"Failed to send error response: {e}")

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
