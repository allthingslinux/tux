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
    TuxPermissionDeniedError,
    TuxPermissionLevelError,
    TuxUnsupportedLanguageError,
)

# Constants
DEFAULT_ERROR_MESSAGE = "An unexpected error occurred. Please try again later."

# Levenshtein suggestion parameters
SHORT_CMD_LEN_THRESHOLD = 3
SHORT_CMD_MAX_SUGGESTIONS = 2
SHORT_CMD_MAX_DISTANCE = 1
DEFAULT_MAX_SUGGESTIONS = 3
DEFAULT_MAX_DISTANCE_THRESHOLD = 3

# Type alias for error detail extractors
ErrorDetailExtractor = Callable[..., dict[str, Any]]


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

    # Whether to suggest similar commands for CommandNotFound
    suggest_similar_commands: bool = True

    # Whether to include command usage in error messages
    include_usage: bool = True


# Import extractors here to avoid circular imports
from .extractors import (
    extract_bad_flag_argument_details,
    extract_bad_union_argument_details,
    extract_httpx_status_details,
    extract_missing_any_role_details,
    extract_missing_flag_details,
    extract_missing_role_details,
    extract_permission_denied_details,
    extract_permissions_details,
)

# Comprehensive error configuration mapping organized by inheritance hierarchy
#
# Organization follows Discord.py's exception hierarchy for proper fallback behavior:
# - Base exceptions at the top (DiscordException, CommandError, etc.)
# - More specific exceptions override parent behavior when needed
# - Error handler walks MRO (__mro__) to find most specific configuration
#
# This ensures proper inheritance-based fallbacks while allowing specific overrides.
ERROR_CONFIG_MAP: dict[type[Exception], ErrorHandlerConfig] = {
    # === Base Exception Classes ===
    discord.DiscordException: ErrorHandlerConfig(
        message_format="A Discord error occurred: {error}",
        log_level="WARNING",
    ),
    app_commands.AppCommandError: ErrorHandlerConfig(
        message_format="An application command error occurred: {error}",
        log_level="WARNING",
    ),
    commands.CommandError: ErrorHandlerConfig(
        message_format="A command error occurred: {error}",
        log_level="WARNING",
    ),
    commands.UserInputError: ErrorHandlerConfig(
        message_format="Invalid input provided.",
        send_to_sentry=False,
    ),
    commands.CheckFailure: ErrorHandlerConfig(
        message_format="You don't meet the requirements for this command.",
        send_to_sentry=False,
    ),
    commands.ExtensionError: ErrorHandlerConfig(
        message_format="Extension error: {error}",
        log_level="WARNING",
    ),
    # === Application Command Hierarchy ===
    app_commands.CheckFailure: ErrorHandlerConfig(
        message_format="You don't meet the requirements for this command.",
        send_to_sentry=False,
    ),
    app_commands.CommandInvokeError: ErrorHandlerConfig(
        message_format="An internal error occurred while running the command.",
        log_level="ERROR",
    ),
    app_commands.TransformerError: ErrorHandlerConfig(
        message_format="Failed to process argument: {error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    app_commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        send_to_sentry=False,
    ),
    app_commands.BotMissingPermissions: ErrorHandlerConfig(
        message_format="I lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        log_level="WARNING",
    ),
    app_commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
    ),
    app_commands.MissingAnyRole: ErrorHandlerConfig(
        message_format="You need one of these roles: {roles}",
        detail_extractor=extract_missing_any_role_details,
        send_to_sentry=False,
    ),
    app_commands.CommandOnCooldown: ErrorHandlerConfig(
        message_format="Command on cooldown. Wait {error.retry_after:.1f}s.",
        send_to_sentry=False,
    ),
    app_commands.NoPrivateMessage: ErrorHandlerConfig(
        message_format="This command cannot be used in direct messages.",
        send_to_sentry=False,
    ),
    app_commands.CommandSignatureMismatch: ErrorHandlerConfig(
        message_format="Command signature mismatch. Please report this.",
        log_level="ERROR",
    ),
    app_commands.CommandNotFound: ErrorHandlerConfig(
        message_format="Application command not found.",
        log_level="INFO",
        send_to_sentry=False,
    ),
    app_commands.CommandAlreadyRegistered: ErrorHandlerConfig(
        message_format="Command already registered.",
        log_level="WARNING",
    ),
    app_commands.CommandLimitReached: ErrorHandlerConfig(
        message_format="Command limit reached.",
        log_level="WARNING",
    ),
    app_commands.CommandSyncFailure: ErrorHandlerConfig(
        message_format="Failed to sync commands with Discord.",
        log_level="ERROR",
    ),
    app_commands.TranslationError: ErrorHandlerConfig(
        message_format="Translation error occurred.",
        log_level="WARNING",
    ),
    # === Traditional Command Hierarchy ===
    commands.CommandInvokeError: ErrorHandlerConfig(
        message_format="An internal error occurred while running the command.",
        log_level="ERROR",
    ),
    commands.ConversionError: ErrorHandlerConfig(
        message_format="Failed to convert argument: {error.original}",
        send_to_sentry=False,
    ),
    commands.BadArgument: ErrorHandlerConfig(
        message_format="Invalid argument: {error}",
        send_to_sentry=False,
    ),
    commands.MissingRequiredArgument: ErrorHandlerConfig(
        message_format="Missing required argument: `{error.param.name}`",
        send_to_sentry=False,
    ),
    commands.MissingRequiredAttachment: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.TooManyArguments: ErrorHandlerConfig(
        message_format="Too many arguments provided.",
        send_to_sentry=False,
    ),
    commands.BadUnionArgument: ErrorHandlerConfig(
        message_format="Invalid argument type: `{argument}`\nExpected: {expected_types}{usage}",
        detail_extractor=extract_bad_union_argument_details,
        send_to_sentry=False,
    ),
    commands.BadLiteralArgument: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.BadBoolArgument: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.RangeError: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.ArgumentParsingError: ErrorHandlerConfig(
        message_format="Failed to parse command arguments: {error}",
        send_to_sentry=False,
    ),
    commands.UnexpectedQuoteError: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.InvalidEndOfQuotedStringError: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.ExpectedClosingQuoteError: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    # === Check Failures ===
    commands.CheckAnyFailure: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.PrivateMessageOnly: ErrorHandlerConfig(
        message_format="This command can only be used in private messages.",
        send_to_sentry=False,
    ),
    commands.NoPrivateMessage: ErrorHandlerConfig(
        message_format="This command cannot be used in private messages.",
        send_to_sentry=False,
    ),
    commands.NotOwner: ErrorHandlerConfig(
        message_format="This command is owner-only.",
        send_to_sentry=False,
    ),
    commands.NSFWChannelRequired: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        send_to_sentry=False,
    ),
    commands.BotMissingPermissions: ErrorHandlerConfig(
        message_format="I lack required permissions: {permissions}",
        detail_extractor=extract_permissions_details,
        log_level="WARNING",
    ),
    commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
    ),
    commands.BotMissingRole: ErrorHandlerConfig(
        message_format="Bot requires the role {roles} to run this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
    ),
    commands.CommandNotFound: ErrorHandlerConfig(
        message_format="Command not found.",
        send_to_sentry=False,
    ),
    commands.CommandOnCooldown: ErrorHandlerConfig(
        message_format="Command on cooldown. Wait {error.retry_after:.1f}s.",
        send_to_sentry=False,
    ),
    commands.MaxConcurrencyReached: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.DisabledCommand: ErrorHandlerConfig(
        message_format="This command is currently disabled.",
        send_to_sentry=False,
    ),
    commands.MissingFlagArgument: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.TooManyFlags: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    # === Flag Errors ===
    commands.FlagError: ErrorHandlerConfig(
        message_format="Flag error: {error}",
        send_to_sentry=False,
    ),
    commands.BadFlagArgument: ErrorHandlerConfig(
        message_format="Invalid flag `{flag_name}`: {original_cause}{usage}",
        detail_extractor=extract_bad_flag_argument_details,
        send_to_sentry=False,
    ),
    commands.MissingRequiredFlag: ErrorHandlerConfig(
        message_format="Missing required flag: `{flag_name}`{usage}",
        detail_extractor=extract_missing_flag_details,
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
    commands.CommandRegistrationError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="WARNING",
    ),
    commands.HybridCommandError: ErrorHandlerConfig(
        message_format="Hybrid command error: {error}",
        log_level="WARNING",
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
    commands.MessageNotFound: ErrorHandlerConfig(
        message_format="Message not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.ChannelNotReadable: ErrorHandlerConfig(
        message_format="Cannot read messages in {error.argument.mention}.",
        send_to_sentry=False,
    ),
    commands.ThreadNotFound: ErrorHandlerConfig(
        message_format="Thread not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.ObjectNotFound: ErrorHandlerConfig(
        message_format="{error.argument!r} does not follow a valid ID or mention format.",
        send_to_sentry=False,
    ),
    commands.BadColourArgument: ErrorHandlerConfig(
        message_format="Invalid color: {error.argument}",
        send_to_sentry=False,
    ),
    commands.BadInviteArgument: ErrorHandlerConfig(
        message_format="Invalid invite: {error.argument}",
        send_to_sentry=False,
    ),
    commands.PartialEmojiConversionFailure: ErrorHandlerConfig(
        message_format="Invalid emoji format: {error.argument}",
        send_to_sentry=False,
    ),
    commands.GuildStickerNotFound: ErrorHandlerConfig(
        message_format="Sticker not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.ScheduledEventNotFound: ErrorHandlerConfig(
        message_format="Scheduled event not found: {error.argument}",
        send_to_sentry=False,
    ),
    commands.SoundboardSoundNotFound: ErrorHandlerConfig(
        message_format="Soundboard sound not found: {error.argument}",
        send_to_sentry=False,
    ),
    # === Client Connection Errors ===
    discord.ConnectionClosed: ErrorHandlerConfig(
        message_format="{error}",
        log_level="WARNING",
    ),
    discord.GatewayNotFound: ErrorHandlerConfig(
        message_format="{error}",
        log_level="ERROR",
    ),
    discord.InvalidData: ErrorHandlerConfig(
        message_format="Invalid data received from Discord.",
        log_level="WARNING",
    ),
    discord.LoginFailure: ErrorHandlerConfig(
        message_format="Failed to authenticate with Discord.",
        log_level="ERROR",
    ),
    discord.PrivilegedIntentsRequired: ErrorHandlerConfig(
        message_format="{error}",
        log_level="ERROR",
    ),
    discord.InteractionResponded: ErrorHandlerConfig(
        message_format="{error}",
        log_level="WARNING",
    ),
    discord.MissingApplicationID: ErrorHandlerConfig(
        message_format="{error}",
        log_level="ERROR",
    ),
    # === Additional Check Failures ===
    commands.CheckAnyFailure: ErrorHandlerConfig(
        message_format="{error}",
        send_to_sentry=False,
    ),
    commands.PrivateMessageOnly: ErrorHandlerConfig(
        message_format="This command can only be used in private messages.",
        send_to_sentry=False,
    ),
    commands.NoPrivateMessage: ErrorHandlerConfig(
        message_format="This command cannot be used in private messages.",
        send_to_sentry=False,
    ),
    commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
    ),
    commands.BotMissingRole: ErrorHandlerConfig(
        message_format="Bot requires the role {roles} to run this command.",
        detail_extractor=extract_missing_role_details,
        send_to_sentry=False,
    ),
    commands.MissingAnyRole: ErrorHandlerConfig(
        message_format="You need one of these roles: {roles}",
        detail_extractor=extract_missing_any_role_details,
        send_to_sentry=False,
    ),
    commands.BotMissingAnyRole: ErrorHandlerConfig(
        message_format="Bot requires one of these roles: {roles}",
        detail_extractor=extract_missing_any_role_details,
        send_to_sentry=False,
    ),
    commands.NSFWChannelRequired: ErrorHandlerConfig(
        message_format="{error}",
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
    ),
    TuxPermissionDeniedError: ErrorHandlerConfig(
        message_format="{message}",
        detail_extractor=extract_permission_denied_details,
        send_to_sentry=False,
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
    # === Discord API Hierarchy ===
    # DiscordException is defined at the top of the file as the base exception
    discord.ClientException: ErrorHandlerConfig(
        message_format="Discord client error: {error}",
        log_level="WARNING",
    ),
    discord.HTTPException: ErrorHandlerConfig(
        message_format="Discord API error: {error.status} {error.text}",
        log_level="WARNING",
    ),
    discord.DiscordServerError: ErrorHandlerConfig(
        message_format="Discord server error: {error.status} {error.text}",
        log_level="ERROR",
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
    discord.RateLimited: ErrorHandlerConfig(
        message_format="Rate limited. Try again in {error.retry_after:.1f}s.",
        log_level="WARNING",
    ),
    discord.ConnectionClosed: ErrorHandlerConfig(
        message_format="Discord connection closed: {error.reason}",
        log_level="WARNING",
    ),
    discord.GatewayNotFound: ErrorHandlerConfig(
        message_format="Discord gateway not found.",
        log_level="ERROR",
    ),
    discord.InvalidData: ErrorHandlerConfig(
        message_format="Invalid data received from Discord: {error}",
        log_level="WARNING",
    ),
    discord.LoginFailure: ErrorHandlerConfig(
        message_format="Failed to login to Discord.",
        log_level="ERROR",
    ),
    discord.PrivilegedIntentsRequired: ErrorHandlerConfig(
        message_format="Missing required privileged intents for this feature.",
        log_level="ERROR",
    ),
    discord.InteractionResponded: ErrorHandlerConfig(
        message_format="Interaction already responded to.",
        log_level="WARNING",
    ),
    discord.MissingApplicationID: ErrorHandlerConfig(
        message_format="Missing Discord application ID.",
        log_level="ERROR",
    ),
}
