"""Error handler configuration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from tux.shared.exceptions import (
    TuxAppCommandPermissionLevelError,
    TuxCodeExecutionError,
    TuxCompilationError,
    TuxInvalidCodeFormatError,
    TuxMissingCodeError,
    TuxPermissionLevelError,
    TuxUnsupportedLanguageError,
)

# Constants
DEFAULT_ERROR_MESSAGE = "An unexpected error occurred. Please try again later."
COMMAND_ERROR_DELETE_AFTER = 30
SUGGESTION_DELETE_AFTER = 15

# Levenshtein suggestion parameters
SHORT_CMD_LEN_THRESHOLD = 3
SHORT_CMD_MAX_SUGGESTIONS = 2
SHORT_CMD_MAX_DISTANCE = 1
DEFAULT_MAX_SUGGESTIONS = 3
DEFAULT_MAX_DISTANCE_THRESHOLD = 3

# Type alias for error detail extractors
ErrorDetailExtractor = Callable[[Exception], dict[str, Any]]


@dataclass
class ErrorHandlerConfig:
    """Configuration for handling a specific error type."""

    # Message format string with placeholders
    message_format: str = DEFAULT_ERROR_MESSAGE

    # Function to extract error-specific details
    detail_extractor: ErrorDetailExtractor | None = None

    # Logging level
    log_level: str = "INFO"

    # Whether to send to Sentry
    send_to_sentry: bool = True

    # Whether to send embed response
    send_embed: bool = True

    # Whether to delete error messages (prefix commands only)
    delete_error_messages: bool = True

    # Delete timeout
    error_message_delete_after: int = COMMAND_ERROR_DELETE_AFTER

    # Whether to suggest similar commands for CommandNotFound
    suggest_similar_commands: bool = True

    # Whether to include command usage in error messages
    include_usage: bool = True

    # Suggestion delete timeout
    suggestion_delete_after: int = SUGGESTION_DELETE_AFTER


# Import extractors here to avoid circular imports
from .extractors import (
    extract_bad_flag_argument_details,
    extract_httpx_status_details,
    extract_missing_any_role_details,
    extract_missing_argument_details,
    extract_missing_flag_details,
    extract_missing_role_details,
    extract_permissions_details,
)

# Comprehensive error configuration mapping
ERROR_CONFIG_MAP: dict[type[Exception], ErrorHandlerConfig] = {
    # === Application Commands ===
    app_commands.AppCommandError: ErrorHandlerConfig(
        message_format="An application command error occurred: {error}",
        log_level="WARNING",
        delete_error_messages=False,
    ),
    app_commands.CommandInvokeError: ErrorHandlerConfig(
        message_format="An internal error occurred while running the command.",
        log_level="ERROR",
        delete_error_messages=False,
    ),
    app_commands.TransformerError: ErrorHandlerConfig(
        message_format="Failed to process argument: {error}",
        log_level="INFO",
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    app_commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    app_commands.MissingAnyRole: ErrorHandlerConfig(
        message_format="You need one of these roles: {roles}",
        detail_extractor=extract_missing_any_role_details,
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    app_commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    app_commands.CheckFailure: ErrorHandlerConfig(
        message_format="You don't meet the requirements for this command.",
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    app_commands.CommandOnCooldown: ErrorHandlerConfig(
        message_format="Command on cooldown. Wait {error.retry_after:.1f}s.",
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    app_commands.BotMissingPermissions: ErrorHandlerConfig(
        message_format="I lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        log_level="WARNING",
        delete_error_messages=False,
    ),
    app_commands.CommandSignatureMismatch: ErrorHandlerConfig(
        message_format="Command signature mismatch. Please report this.",
        log_level="ERROR",
        delete_error_messages=False,
    ),
    # === Traditional Commands ===
    commands.CommandError: ErrorHandlerConfig(
        message_format="A command error occurred: {error}",
        log_level="WARNING",
    ),
    commands.CommandInvokeError: ErrorHandlerConfig(
        message_format="An internal error occurred while running the command.",
        log_level="ERROR",
    ),
    commands.ConversionError: ErrorHandlerConfig(
        message_format="Failed to convert argument: {error.original}",
        send_to_sentry=False,
    ),
    commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
    ),
    commands.MissingAnyRole: ErrorHandlerConfig(
        message_format="You need one of these roles: {roles}",
        detail_extractor=extract_missing_any_role_details,
        send_to_sentry=False,
    ),
    commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        send_to_sentry=False,
    ),
    commands.FlagError: ErrorHandlerConfig(
        message_format="Flag error: {error}\nUsage: `{ctx.prefix}{usage}`",
        send_to_sentry=False,
    ),
    commands.BadFlagArgument: ErrorHandlerConfig(
        message_format="Invalid flag `{flag_name}`: {original_cause}\nUsage: `{ctx.prefix}{usage}`",
        detail_extractor=extract_bad_flag_argument_details,
        send_to_sentry=False,
    ),
    commands.MissingRequiredFlag: ErrorHandlerConfig(
        message_format="Missing required flag: `{flag_name}`\nUsage: `{ctx.prefix}{usage}`",
        detail_extractor=extract_missing_flag_details,
        send_to_sentry=False,
    ),
    commands.CheckFailure: ErrorHandlerConfig(
        message_format="You don't meet the requirements for this command.",
        send_to_sentry=False,
    ),
    commands.CommandOnCooldown: ErrorHandlerConfig(
        message_format="Command on cooldown. Wait {error.retry_after:.1f}s.",
        send_to_sentry=False,
    ),
    commands.MissingRequiredArgument: ErrorHandlerConfig(
        message_format="Missing argument: `{param_name}`\nUsage: `{ctx.prefix}{usage}`",
        detail_extractor=extract_missing_argument_details,
        send_to_sentry=False,
    ),
    commands.TooManyArguments: ErrorHandlerConfig(
        message_format="Too many arguments.\nUsage: `{ctx.prefix}{usage}`",
        send_to_sentry=False,
    ),
    commands.NotOwner: ErrorHandlerConfig(
        message_format="This command is owner-only.",
        send_to_sentry=False,
    ),
    commands.BotMissingPermissions: ErrorHandlerConfig(
        message_format="I lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        log_level="WARNING",
    ),
    commands.BadArgument: ErrorHandlerConfig(
        message_format="Invalid argument: {error}",
        send_to_sentry=False,
    ),
    # === Extension Management Errors ===
    commands.ExtensionAlreadyLoaded: ErrorHandlerConfig(
        message_format="Extension `{error.name}` is already loaded.",
        send_to_sentry=False,
    ),
    commands.ExtensionNotLoaded: ErrorHandlerConfig(
        message_format="Extension `{error.name}` is not loaded.",
        send_to_sentry=False,
    ),
    commands.ExtensionNotFound: ErrorHandlerConfig(
        message_format="Extension `{error.name}` not found.",
        send_to_sentry=False,
    ),
    commands.NoEntryPointError: ErrorHandlerConfig(
        message_format="Extension `{error.name}` has no setup function.",
        send_to_sentry=False,
    ),
    commands.ExtensionFailed: ErrorHandlerConfig(
        message_format="Extension `{error.name}` failed to load: {error.original}",
        log_level="ERROR",
    ),
    # === Entity Not Found Errors ===
    commands.MemberNotFound: ErrorHandlerConfig(
        message_format="Member not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.UserNotFound: ErrorHandlerConfig(
        message_format="User not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.ChannelNotFound: ErrorHandlerConfig(
        message_format="Channel not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.RoleNotFound: ErrorHandlerConfig(
        message_format="Role not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.EmojiNotFound: ErrorHandlerConfig(
        message_format="Emoji not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.GuildNotFound: ErrorHandlerConfig(
        message_format="Server not found: {error.argument}",
        send_to_sentry=False,
    ),
    # === Custom Errors ===
    TuxPermissionLevelError: ErrorHandlerConfig(
        message_format="You need permission level `{error.permission}`.",
        send_to_sentry=False,
    ),
    TuxAppCommandPermissionLevelError: ErrorHandlerConfig(
        message_format="You need permission level `{error.permission}`.",
        send_to_sentry=False,
        delete_error_messages=False,
    ),
    TuxMissingCodeError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    TuxInvalidCodeFormatError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    TuxUnsupportedLanguageError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    TuxCompilationError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
    ),
    TuxCodeExecutionError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
    ),
    # === HTTPX Errors ===
    httpx.HTTPError: ErrorHandlerConfig(
        message_format="Network error occurred: {error}",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    httpx.RequestError: ErrorHandlerConfig(
        message_format="Request failed: {error}",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    httpx.HTTPStatusError: ErrorHandlerConfig(
        message_format="HTTP {status_code} error from {url}: {response_text}",
        detail_extractor=extract_httpx_status_details,
        log_level="WARNING",
        send_to_sentry=True,
    ),
    httpx.TimeoutException: ErrorHandlerConfig(
        message_format="Request timed out. Please try again later.",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    httpx.ConnectError: ErrorHandlerConfig(
        message_format="Connection failed. Service may be unavailable.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    httpx.ReadTimeout: ErrorHandlerConfig(
        message_format="Request timed out while reading response.",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    httpx.WriteTimeout: ErrorHandlerConfig(
        message_format="Request timed out while sending data.",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    httpx.PoolTimeout: ErrorHandlerConfig(
        message_format="Connection pool timeout. Too many concurrent requests.",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    # === Discord API Errors ===
    discord.HTTPException: ErrorHandlerConfig(
        message_format="Discord API error: {error.status} {error.text}",
        log_level="WARNING",
    ),
    discord.RateLimited: ErrorHandlerConfig(
        message_format="Rate limited. Try again in {error.retry_after:.1f}s.",
        log_level="WARNING",
    ),
    discord.Forbidden: ErrorHandlerConfig(
        message_format="Permission denied: {error.text}",
        log_level="WARNING",
    ),
    discord.NotFound: ErrorHandlerConfig(
        message_format="Resource not found: {error.text}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    discord.InteractionResponded: ErrorHandlerConfig(
        message_format="Interaction already responded to.",
        log_level="WARNING",
    ),
}
