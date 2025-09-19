"""Error message formatting utilities."""

import typing

import discord
from discord import app_commands
from discord.ext import commands

from tux.shared.exceptions import (
    AppCommandPermissionLevelError,
    CodeExecutionError,
    CompilationError,
    InvalidCodeFormatError,
    MissingCodeError,
    PermissionLevelError,
    UnsupportedLanguageError,
)

from .config import DEFAULT_ERROR_MESSAGE, ErrorHandlerConfig
from .extractors import (
    extract_bad_flag_argument_details,
    extract_missing_any_role_details,
    extract_missing_argument_details,
    extract_missing_flag_details,
    extract_missing_role_details,
    extract_permissions_details,
    fallback_format_message,
)

# Error configuration mapping for different error types
ERROR_CONFIG_MAP: dict[type[Exception], ErrorHandlerConfig] = {
    # === Application Commands (discord.app_commands) ===
    app_commands.AppCommandError: ErrorHandlerConfig(
        delete_error_messages=False,  # App commands are ephemeral by default
        suggest_similar_commands=False,
    ),
    # === Traditional Commands (discord.ext.commands) ===
    commands.CommandError: ErrorHandlerConfig(
        delete_error_messages=True,
        suggest_similar_commands=True,
    ),
    # === Permission Errors ===
    commands.MissingPermissions: ErrorHandlerConfig(
        delete_error_messages=True,
        suggest_similar_commands=False,
    ),
    commands.BotMissingPermissions: ErrorHandlerConfig(
        delete_error_messages=True,
        suggest_similar_commands=False,
    ),
    # === Custom Errors ===
    PermissionLevelError: ErrorHandlerConfig(
        delete_error_messages=True,
        suggest_similar_commands=False,
    ),
    AppCommandPermissionLevelError: ErrorHandlerConfig(
        delete_error_messages=False,
        suggest_similar_commands=False,
    ),
}


class ErrorFormatter:
    """Formats error messages into user-friendly embeds."""

    # Error message templates for different error types
    ERROR_MESSAGES: typing.ClassVar[dict[type[Exception], str]] = {
        # Permission-related errors
        commands.MissingPermissions: "You don't have the required permissions: {missing_permissions}",
        commands.BotMissingPermissions: "I don't have the required permissions: {missing_permissions}",
        commands.MissingRole: "You don't have the required role: `{missing_role}`",
        commands.BotMissingRole: "I don't have the required role: `{missing_role}`",
        commands.MissingAnyRole: "You don't have any of the required roles: {missing_roles}",
        commands.BotMissingAnyRole: "I don't have any of the required roles: {missing_roles}",
        commands.NotOwner: "This command can only be used by the bot owner.",
        PermissionLevelError: "You don't have the required permission level to use this command.",
        AppCommandPermissionLevelError: "You don't have the required permission level to use this command.",
        # Command usage errors
        commands.MissingRequiredArgument: "Missing required argument: `{param_name}`",
        commands.BadArgument: "Invalid argument provided. Please check your input and try again.",
        commands.BadUnionArgument: "Invalid argument type. Please check the expected format.",
        commands.BadLiteralArgument: "Invalid choice. Please select from the available options.",
        commands.ArgumentParsingError: "Error parsing arguments. Please check your input format.",
        commands.TooManyArguments: "Too many arguments provided.",
        commands.BadFlagArgument: "Invalid flag argument for `{flag_name}`.",
        commands.MissingFlagArgument: "Missing required flag: `{flag_name}`",
        commands.TooManyFlags: "Too many flags provided.",
        # Command state errors
        commands.CommandOnCooldown: "This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
        commands.MaxConcurrencyReached: "This command is already running. Please wait for it to finish.",
        commands.DisabledCommand: "This command is currently disabled.",
        commands.CheckFailure: "You don't have permission to use this command.",
        commands.CheckAnyFailure: "You don't meet any of the required conditions for this command.",
        # Code execution errors (custom)
        MissingCodeError: "No code provided. Please include code in your message.",
        InvalidCodeFormatError: "Invalid code format. Please use proper code blocks.",
        UnsupportedLanguageError: "Unsupported programming language: `{error.language}`",
        CompilationError: "Code compilation failed:\n```\n{error.message}\n```",
        CodeExecutionError: "Code execution failed:\n```\n{error.message}\n```",
        # Generic errors
        commands.CommandError: "An error occurred while executing the command.",
        Exception: DEFAULT_ERROR_MESSAGE,
    }
    # Error detail extractors for specific error types
    ERROR_EXTRACTORS: typing.ClassVar[dict[type[Exception], typing.Callable[[Exception], dict[str, typing.Any]]]] = {
        commands.MissingPermissions: extract_permissions_details,
        commands.BotMissingPermissions: extract_permissions_details,
        commands.MissingRole: extract_missing_role_details,
        commands.BotMissingRole: extract_missing_role_details,
        commands.MissingAnyRole: extract_missing_any_role_details,
        commands.BotMissingAnyRole: extract_missing_any_role_details,
        commands.MissingRequiredArgument: extract_missing_argument_details,
        commands.BadFlagArgument: extract_bad_flag_argument_details,
        commands.MissingFlagArgument: extract_missing_flag_details,
    }

    def format_error_embed(self, error: Exception, command_signature: str | None = None) -> discord.Embed:
        """
        Creates a user-friendly error embed for the given exception.

        Args:
            error: The exception that occurred.
            command_signature: Optional command signature for context.

        Returns:
            A Discord embed containing the formatted error message.
        """
        error_type = type(error)

        # Find the most specific error message template
        message_template = self._get_error_message_template(error_type)

        # Extract error-specific details
        error_details = self._extract_error_details(error)

        # Format the message with error details
        try:
            formatted_message = message_template.format(error=error, **error_details)
        except (KeyError, AttributeError, ValueError):
            formatted_message = fallback_format_message(message_template, error)

        # Create the embed
        embed = discord.Embed(
            title="Command Error",
            description=formatted_message,
            color=discord.Color.red(),
        )

        # Add command signature if available
        if command_signature:
            embed.add_field(
                name="Usage",
                value=f"`{command_signature}`",
                inline=False,
            )

        return embed

    def _get_error_message_template(self, error_type: type) -> str:
        # sourcery skip: use-next
        """Get the most appropriate error message template for the error type."""
        # Check for exact match first
        if error_type in self.ERROR_MESSAGES:
            return self.ERROR_MESSAGES[error_type]

        # Check parent classes (MRO - Method Resolution Order)
        for base_type in error_type.__mro__:
            if base_type in self.ERROR_MESSAGES:
                return self.ERROR_MESSAGES[base_type]

        # Fallback to generic error message
        return DEFAULT_ERROR_MESSAGE

    def _extract_error_details(self, error: Exception) -> dict[str, str]:
        # sourcery skip: use-next
        """Extract error-specific details using the appropriate extractor."""
        error_type = type(error)

        # Check for exact match first
        if error_type in self.ERROR_EXTRACTORS:
            return self.ERROR_EXTRACTORS[error_type](error)

        # Check parent classes
        for base_type in error_type.__mro__:
            if base_type in self.ERROR_EXTRACTORS:
                return self.ERROR_EXTRACTORS[base_type](error)

        # No specific extractor found
        return {}
