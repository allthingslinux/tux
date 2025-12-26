"""Error message formatting utilities."""

from contextlib import suppress
from typing import Any

import discord
from discord.ext import commands

from tux.core.bot import Tux

from .config import ERROR_CONFIG_MAP, ErrorHandlerConfig
from .extractors import fallback_format_message


class ErrorFormatter:
    """Formats errors into user-friendly Discord embeds."""

    def format_error_embed(
        self,
        error: Exception,
        source: commands.Context[Tux] | discord.Interaction,
        config: ErrorHandlerConfig,
    ) -> discord.Embed:
        """Create user-friendly error embed.

        Returns
        -------
        discord.Embed
            Formatted error embed for display.
        """
        # Format the error message
        message = self._format_error_message(error, source, config)

        # Create embed
        embed = discord.Embed(
            title="Command Error",
            description=message,
            color=discord.Color.red(),
        )

        # Add command usage if available and configured
        if (
            config.include_usage
            and isinstance(source, commands.Context)
            and (usage := self._get_command_usage(source))
        ):
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        return embed

    def _format_error_message(
        self,
        error: Exception,
        source: commands.Context[Tux] | discord.Interaction,
        config: ErrorHandlerConfig,
    ) -> str:
        """Format error message using configuration.

        Returns
        -------
        str
            Formatted error message.
        """
        message_format = config.message_format
        kwargs: dict[str, Any] = {"error": error}

        # Add context for commands (both traditional and slash)
        if isinstance(source, commands.Context):
            kwargs["ctx"] = source
            kwargs["source"] = source  # Also add as generic source
            if source.command and "{usage}" in message_format:
                kwargs["usage"] = self._get_command_usage(source)
        else:  # Must be discord.Interaction
            kwargs["interaction"] = source
            kwargs["source"] = source  # Add as generic source

        # Extract error-specific details
        if config.detail_extractor:
            with suppress(Exception):
                # Remove 'error' from kwargs to avoid conflicts with positional parameter
                extractor_kwargs = {k: v for k, v in kwargs.items() if k != "error"}
                details = config.detail_extractor(error, **extractor_kwargs)
                kwargs |= details

        # Format message with fallback
        try:
            return message_format.format(**kwargs)
        except Exception:
            # format() can raise KeyError, ValueError, IndexError, etc. for invalid placeholders
            # Catching Exception is appropriate here as we want to fall back to safe formatting
            return fallback_format_message(message_format, error)

    def _get_command_usage(self, ctx: commands.Context[Tux]) -> str | None:
        """Get command usage string.

        Returns
        -------
        str | None
            Command usage string if available, None otherwise.
        """
        if not ctx.command:
            return None

        prefix = ctx.prefix

        # Use the command's usage attribute if it exists (e.g., custom generated usage)
        if ctx.command.usage:
            return f"{prefix}{ctx.command.usage}"

        # Otherwise, construct from signature
        signature = ctx.command.signature.strip()
        qualified_name = ctx.command.qualified_name

        return f"{prefix}{qualified_name}{f' {signature}' if signature else ''}"

    def get_error_config(self, error: Exception) -> ErrorHandlerConfig:
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
