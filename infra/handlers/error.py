"""
Handles errors originating from both traditional (prefix) and application (slash) commands.

This module implements a centralized error handling mechanism for the Tux bot,
adhering to principles like structured logging and robust handling of failures
within the handler itself. It distinguishes between user-correctable errors (like
missing permissions) and unexpected internal errors, logging them accordingly and
notifying Sentry for unexpected issues.
"""

import contextlib
import traceback
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import discord
import Levenshtein
import sentry_sdk
from discord import app_commands
from discord.ext import commands
from loguru import logger

from core.bot import Tux
from core.ui.embeds import EmbedCreator
from core.utils.exceptions import (
    AppCommandPermissionLevelError,
    CodeExecutionError,
    CompilationError,
    InvalidCodeFormatError,
    MissingCodeError,
    PermissionLevelError,
    UnsupportedLanguageError,
)

# --- Constants and Configuration ---

# Default message displayed to the user when an unhandled error occurs
# or when formatting a specific error message fails.
DEFAULT_ERROR_MESSAGE: str = "An unexpected error occurred. Please try again later."

# Default time in seconds before attempting to delete error messages sent
# via traditional (prefix) commands. This helps keep channels cleaner.
COMMAND_ERROR_DELETE_AFTER: int = 30

# Default time in seconds before deleting the 'Did you mean?' command suggestion message.
# This provides temporary assistance without persistent channel clutter.
SUGGESTION_DELETE_AFTER: int = 15

# --- Levenshtein Suggestion Parameters ---
# These parameters control the behavior of the command suggestion feature,
# which uses the Levenshtein distance algorithm to find similar command names.

# Commands with names shorter than or equal to this length use stricter matching parameters.
SHORT_CMD_LEN_THRESHOLD: int = 3
# Maximum number of suggestions to provide for short command names.
SHORT_CMD_MAX_SUGGESTIONS: int = 2
# Maximum Levenshtein distance allowed for suggestions for short command names.
SHORT_CMD_MAX_DISTANCE: int = 1
# Default maximum number of suggestions to provide for longer command names.
DEFAULT_MAX_SUGGESTIONS: int = 3
# Default maximum Levenshtein distance allowed for suggestions for longer command names.
DEFAULT_MAX_DISTANCE_THRESHOLD: int = 3


# --- Type Aliases and Definitions ---

# Represents either a traditional command context or an application command interaction.
ContextOrInteraction = commands.Context[Tux] | discord.Interaction

# Signature for functions that extract specific details from an error object.
ErrorDetailExtractor = Callable[[Exception], dict[str, Any]]

# Signature for the application command error handler expected by `discord.py`.
# Note: Interaction is parameterized with the Bot type (Tux).
AppCommandErrorHandler = Callable[[discord.Interaction[Tux], app_commands.AppCommandError], Coroutine[Any, Any, None]]

# --- Sentry Status Constants (copied from sentry.py for local use) ---
SENTRY_STATUS_OK = "ok"
SENTRY_STATUS_UNKNOWN = "unknown"
SENTRY_STATUS_INTERNAL_ERROR = "internal_error"
SENTRY_STATUS_NOT_FOUND = "not_found"
SENTRY_STATUS_PERMISSION_DENIED = "permission_denied"
SENTRY_STATUS_INVALID_ARGUMENT = "invalid_argument"
SENTRY_STATUS_RESOURCE_EXHAUSTED = "resource_exhausted"


# --- Error Handler Configuration ---


@dataclass
class ErrorHandlerConfig:
    """Stores configuration for handling a specific type of exception."""

    # User-facing message format string. Can include placeholders like {error}, {permissions}, etc.
    message_format: str

    # Optional function to extract specific details (e.g., role names) for the message format.
    detail_extractor: ErrorDetailExtractor | None = None

    # Default log level for this error type (e.g., "INFO", "WARNING", "ERROR").
    log_level: str = "INFO"

    # Whether to send this specific error type to Sentry when handled.
    # Useful for tracking frequency even if the user sees a friendly message.
    send_to_sentry: bool = True


# --- Helper Functions ---


def _format_list(items: list[str]) -> str:
    """Formats a list of strings into a user-friendly, comma-separated list of code blocks."""
    return ", ".join(f"`{item}`" for item in items) if items else "(none)"


# New helper function for unwrapping errors
def _unwrap_error(error: Any) -> Exception:
    """Unwraps nested errors (like CommandInvokeError) to find the root cause."""
    current = error
    loops = 0
    max_loops = 10  # Safety break
    while hasattr(current, "original") and loops < max_loops:
        next_error = current.original
        if next_error is current:  # Prevent self-referential loops
            logger.warning("Detected self-referential loop in error unwrapping.")
            break
        current = next_error
        loops += 1
    if loops >= max_loops:
        logger.warning(f"Error unwrapping exceeded max depth ({max_loops}).")

    # If unwrapping resulted in something other than an Exception, wrap it.
    if not isinstance(current, Exception):
        logger.warning(f"Unwrapped error is not an Exception: {type(current).__name__}. Wrapping in ValueError.")
        return ValueError(f"Non-exception error encountered after unwrapping: {current!r}")
    return current


# New helper function for fallback message formatting
def _fallback_format_message(message_format: str, error: Exception) -> str:
    """Attempts fallback formatting if the primary format call fails."""

    # Fallback 1: Try formatting with only {error} if it seems possible.
    with contextlib.suppress(Exception):
        # Heuristic: Check if only {error...} seems to be the placeholder used.
        if "{error" in message_format and "{" not in message_format.replace("{error", ""):
            return message_format.format(error=error)

    # Fallback 2: Use the global default message, adding the error string.
    try:
        return f"{DEFAULT_ERROR_MESSAGE} ({error!s})"
    except Exception:
        # Fallback 3: Absolute last resort.
        return DEFAULT_ERROR_MESSAGE


# --- Error Detail Extractors ---
# These functions are specifically designed to pull relevant information from different
# discord.py exception types to make the user-facing error messages more informative.
# They return dictionaries that are used to update the formatting keyword arguments.


def _extract_missing_role_details(error: Exception) -> dict[str, Any]:
    """Extracts the missing role name or ID from MissingRole errors."""
    role_identifier = getattr(error, "missing_role", None)
    # Format as mention if it's an ID, otherwise as code block.
    if isinstance(role_identifier, int):
        return {"roles": f"<@&{role_identifier}>"}
    if isinstance(role_identifier, str):
        return {"roles": f"`{role_identifier}`"}
    return {"roles": "(unknown role)"}


def _extract_missing_any_role_details(error: Exception) -> dict[str, Any]:
    """Extracts the list of missing roles from MissingAnyRole errors."""
    roles_list = getattr(error, "missing_roles", [])
    formatted_roles: list[str] = []
    for r in roles_list:
        # Format role IDs as mentions, names as code blocks.
        if isinstance(r, int):
            formatted_roles.append(f"<@&{r}>")
        else:
            formatted_roles.append(f"`{r!s}`")
    return {"roles": ", ".join(formatted_roles) if formatted_roles else "(unknown roles)"}


def _extract_permissions_details(error: Exception) -> dict[str, Any]:
    """Extracts the list of missing permissions from permission-related errors."""
    perms = getattr(error, "missing_perms", [])
    return {"permissions": _format_list(perms)}


def _extract_bad_flag_argument_details(error: Exception) -> dict[str, Any]:
    """Extracts the flag name and original cause from BadFlagArgument errors."""
    # Safely access potentially nested attributes.
    flag_name = getattr(getattr(error, "flag", None), "name", "unknown_flag")
    original_cause = getattr(error, "original", error)
    return {"flag_name": flag_name, "original_cause": original_cause}


def _extract_missing_flag_details(error: Exception) -> dict[str, Any]:
    """Extracts the missing flag name from MissingRequiredFlag errors."""
    flag_name = getattr(getattr(error, "flag", None), "name", "unknown_flag")
    return {"flag_name": flag_name}


def _extract_missing_argument_details(error: Exception) -> dict[str, Any]:
    """Extracts the missing argument/parameter name from MissingRequiredArgument errors."""
    param_name = getattr(getattr(error, "param", None), "name", "unknown_argument")
    return {"param_name": param_name}


# --- Error Mapping Configuration ---
# This dictionary is the central configuration for how different exception types are handled.
# It maps specific exception classes (keys) to ErrorHandlerConfig objects (values),
# defining the user message, detail extraction logic, logging level, and Sentry reporting behavior.
# Adding or modifying error handling primarily involves updating this dictionary.

ERROR_CONFIG_MAP: dict[type[Exception], ErrorHandlerConfig] = {
    # === Application Commands (discord.app_commands) ===
    app_commands.AppCommandError: ErrorHandlerConfig(
        message_format="An application command error occurred: {error}",
        log_level="WARNING",
    ),
    # CommandInvokeError wraps the actual exception raised within an app command.
    # It will be unwrapped in _handle_error, but this provides a fallback config.
    app_commands.CommandInvokeError: ErrorHandlerConfig(
        message_format="An internal error occurred while running the command.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    app_commands.TransformerError: ErrorHandlerConfig(
        message_format="Failed to process an argument value: {error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    app_commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=_extract_missing_role_details,
        send_to_sentry=False,
    ),
    app_commands.MissingAnyRole: ErrorHandlerConfig(
        message_format="You need one of the following roles: {roles}",
        detail_extractor=_extract_missing_any_role_details,
        send_to_sentry=False,
    ),
    app_commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack the required permission(s): {permissions}",
        detail_extractor=_extract_permissions_details,
        send_to_sentry=False,
    ),
    # Generic check failure for app commands.
    app_commands.CheckFailure: ErrorHandlerConfig(
        message_format="You do not meet the requirements to run this command.",
        send_to_sentry=False,
    ),
    app_commands.CommandOnCooldown: ErrorHandlerConfig(
        message_format="This command is on cooldown. Please wait {error.retry_after:.1f}s.",
        send_to_sentry=False,
    ),
    app_commands.BotMissingPermissions: ErrorHandlerConfig(
        message_format="I lack the required permission(s): {permissions}",
        detail_extractor=_extract_permissions_details,
        log_level="WARNING",
        send_to_sentry=True,
    ),
    # Indicates a mismatch between the command signature registered with Discord
    # and the signature defined in the bot's code.
    app_commands.CommandSignatureMismatch: ErrorHandlerConfig(
        message_format="Internal error: Command signature mismatch. Please report this.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # === Traditional Commands (discord.ext.commands) ===
    commands.CommandError: ErrorHandlerConfig(
        message_format="A command error occurred: {error}",
        log_level="WARNING",
    ),
    # CommandInvokeError wraps the actual exception raised within a prefix command.
    # It will be unwrapped in _handle_error, but this provides a fallback config.
    commands.CommandInvokeError: ErrorHandlerConfig(
        message_format="An internal error occurred while running the command.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    commands.ConversionError: ErrorHandlerConfig(
        message_format="Failed to convert argument: {error.original}",
        send_to_sentry=False,
    ),
    commands.MissingRole: ErrorHandlerConfig(
        message_format="You need the role {roles} to use this command.",
        detail_extractor=_extract_missing_role_details,
        send_to_sentry=False,
    ),
    commands.MissingAnyRole: ErrorHandlerConfig(
        message_format="You need one of the following roles: {roles}",
        detail_extractor=_extract_missing_any_role_details,
        send_to_sentry=False,
    ),
    commands.MissingPermissions: ErrorHandlerConfig(
        message_format="You lack the required permission(s): {permissions}",
        detail_extractor=_extract_permissions_details,
        send_to_sentry=False,
    ),
    # Error related to command flags (discord.ext.flags).
    commands.FlagError: ErrorHandlerConfig(
        message_format="Error processing command flags: {error}\nUsage: `{ctx.prefix}{usage}`",
        send_to_sentry=False,
    ),
    commands.BadFlagArgument: ErrorHandlerConfig(
        message_format="Invalid value for flag `{flag_name}`: {original_cause}\nUsage: `{ctx.prefix}{usage}`",
        detail_extractor=_extract_bad_flag_argument_details,
        send_to_sentry=False,
    ),
    commands.MissingRequiredFlag: ErrorHandlerConfig(
        message_format="Missing required flag: `{flag_name}`\nUsage: `{ctx.prefix}{usage}`",
        detail_extractor=_extract_missing_flag_details,
        send_to_sentry=False,
    ),
    # Generic check failure for prefix commands.
    commands.CheckFailure: ErrorHandlerConfig(
        message_format="You do not meet the requirements to run this command.",
        send_to_sentry=False,
    ),
    commands.CommandOnCooldown: ErrorHandlerConfig(
        message_format="This command is on cooldown. Please wait {error.retry_after:.1f}s.",
        send_to_sentry=False,
    ),
    commands.MissingRequiredArgument: ErrorHandlerConfig(
        message_format="Missing required argument: `{param_name}`\nUsage: `{ctx.prefix}{usage}`",
        detail_extractor=_extract_missing_argument_details,
        send_to_sentry=False,
    ),
    commands.TooManyArguments: ErrorHandlerConfig(
        message_format="You provided too many arguments.\nUsage: `{ctx.prefix}{usage}`",
        send_to_sentry=False,
    ),
    commands.NotOwner: ErrorHandlerConfig(
        message_format="This command can only be used by the bot owner.",
        send_to_sentry=False,
    ),
    commands.BotMissingPermissions: ErrorHandlerConfig(
        message_format="I lack the required permission(s): {permissions}",
        detail_extractor=_extract_permissions_details,
        log_level="WARNING",
        send_to_sentry=True,
    ),
    # Generic bad argument error.
    commands.BadArgument: ErrorHandlerConfig(
        message_format="Invalid argument provided: {error}",
        send_to_sentry=False,
    ),
    # Errors for when specific Discord entities are not found.
    commands.MemberNotFound: ErrorHandlerConfig(
        message_format="Could not find member: {error.argument}.",
        send_to_sentry=False,
    ),
    commands.UserNotFound: ErrorHandlerConfig(
        message_format="Could not find user: {error.argument}.",
        send_to_sentry=False,
    ),
    commands.ChannelNotFound: ErrorHandlerConfig(
        message_format="Could not find channel: {error.argument}.",
        send_to_sentry=False,
    ),
    commands.RoleNotFound: ErrorHandlerConfig(
        message_format="Could not find role: {error.argument}.",
        send_to_sentry=False,
    ),
    commands.EmojiNotFound: ErrorHandlerConfig(
        message_format="Could not find emoji: {error.argument}.",
        send_to_sentry=False,
    ),
    commands.GuildNotFound: ErrorHandlerConfig(
        message_format="Could not find server: {error.argument}.",
        send_to_sentry=False,
    ),
    # === Extension/Cog Loading Errors (discord.ext.commands) ===
    commands.ExtensionError: ErrorHandlerConfig(
        message_format="Extension operation failed: {error}",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    commands.ExtensionNotLoaded: ErrorHandlerConfig(
        message_format="Cannot reload extension `{error.name}` - it hasn't been loaded yet.",
        log_level="WARNING",
        send_to_sentry=False,
    ),
    commands.ExtensionNotFound: ErrorHandlerConfig(
        message_format="Extension `{error.name}` could not be found.",
        log_level="WARNING",
        send_to_sentry=False,
    ),
    commands.ExtensionAlreadyLoaded: ErrorHandlerConfig(
        message_format="Extension `{error.name}` is already loaded.",
        log_level="INFO",
        send_to_sentry=False,
    ),
    commands.ExtensionFailed: ErrorHandlerConfig(
        message_format="Extension `{error.name}` failed to load: {error.original}",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    commands.NoEntryPointError: ErrorHandlerConfig(
        message_format="Extension `{error.name}` is missing a setup function.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # === Custom Errors (defined in tux.utils.exceptions) ===
    PermissionLevelError: ErrorHandlerConfig(
        message_format="You need permission level `{error.permission}` to use this command.",
        send_to_sentry=False,
    ),
    AppCommandPermissionLevelError: ErrorHandlerConfig(
        message_format="You need permission level `{error.permission}` to use this command.",
        send_to_sentry=False,
    ),
    # === Code Execution Errors (from utils.exceptions) ===
    MissingCodeError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    InvalidCodeFormatError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    UnsupportedLanguageError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    CompilationError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=True,  # Monitor frequency of compilation failures
    ),
    CodeExecutionError: ErrorHandlerConfig(
        message_format="{error}",
        log_level="INFO",
        send_to_sentry=True,  # Monitor general code execution issues
    ),
    # === Discord API & Client Errors ===
    discord.ClientException: ErrorHandlerConfig(
        message_format="A client-side error occurred: {error}",
        log_level="WARNING",
        send_to_sentry=True,  # Monitor frequency of generic client errors
    ),
    discord.HTTPException: ErrorHandlerConfig(
        message_format="An HTTP error occurred while communicating with Discord: {error.status} {error.text}",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    discord.RateLimited: ErrorHandlerConfig(
        message_format="We are being rate-limited by Discord. Please try again in {error.retry_after:.1f} seconds.",
        log_level="WARNING",
        send_to_sentry=True,  # Track rate limits
    ),
    # Generic Forbidden/NotFound often indicate deleted resources or permission issues caught by more specific exceptions.
    # These provide fallbacks.
    discord.Forbidden: ErrorHandlerConfig(
        message_format="I don't have permission to perform that action. Error: {error.text}",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    discord.NotFound: ErrorHandlerConfig(
        message_format="Could not find the requested resource (it might have been deleted). Error: {error.text}",
        log_level="INFO",
        send_to_sentry=False,
    ),
    discord.DiscordServerError: ErrorHandlerConfig(
        message_format="Discord reported a server error ({error.status}). Please try again later. Error: {error.text}",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # Indicates unexpected data from Discord, potentially a library or API issue.
    discord.InvalidData: ErrorHandlerConfig(
        message_format="Received invalid data from Discord. Please report this if it persists.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # Specific to interactions, raised if interaction.response.send_message is called more than once.
    discord.InteractionResponded: ErrorHandlerConfig(
        message_format="This interaction has already been responded to.",
        log_level="WARNING",  # Usually indicates a logic error in command code
        send_to_sentry=True,
    ),
    # Raised when Application ID is needed but not available (e.g., for app command sync).
    discord.MissingApplicationID: ErrorHandlerConfig(
        message_format="Internal setup error: Missing Application ID.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # === Common Python Built-in Errors ===
    # These usually indicate internal logic errors, so show a generic message to the user
    # but log them as errors and report to Sentry for debugging.
    ValueError: ErrorHandlerConfig(
        message_format="An internal error occurred due to an invalid value.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    TypeError: ErrorHandlerConfig(
        message_format="An internal error occurred due to a type mismatch.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    KeyError: ErrorHandlerConfig(
        message_format="An internal error occurred while looking up data.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    IndexError: ErrorHandlerConfig(
        message_format="An internal error occurred while accessing a sequence.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    AttributeError: ErrorHandlerConfig(
        message_format="An internal error occurred while accessing an attribute.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    ZeroDivisionError: ErrorHandlerConfig(
        message_format="An internal error occurred during a calculation (division by zero).",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # === Additional Discord Client/Connection Errors ===
    discord.LoginFailure: ErrorHandlerConfig(
        message_format="Bot authentication failed. Please check the bot token configuration.",
        log_level="CRITICAL",
        send_to_sentry=True,
    ),
    discord.ConnectionClosed: ErrorHandlerConfig(
        message_format="Connection to Discord was closed unexpectedly. Attempting to reconnect...",
        log_level="WARNING",
        send_to_sentry=True,
    ),
    discord.PrivilegedIntentsRequired: ErrorHandlerConfig(
        message_format="This bot requires privileged intents to function properly. Please enable them in the Discord Developer Portal.",
        log_level="CRITICAL",
        send_to_sentry=True,
    ),
    discord.GatewayNotFound: ErrorHandlerConfig(
        message_format="Could not connect to Discord's gateway. This may be a temporary issue.",
        log_level="ERROR",
        send_to_sentry=True,
    ),
    # Note: InvalidArgument, NoMoreItems, and TooManyRequests are not available in all discord.py versions
    # or are handled by other existing exceptions like HTTPException
}


# --- Error Handling Cog ---


class ErrorHandler(commands.Cog):
    """
    Cog responsible for centralized error handling for all commands.

    This cog intercepts errors from both traditional prefix commands (via the
    `on_command_error` event listener) and application (slash) commands (by
    overwriting `bot.tree.on_error`). It uses the `ERROR_CONFIG_MAP` to
    determine how to handle known errors and provides robust logging and
    Sentry reporting for both known and unknown exceptions.
    """

    def __init__(self, bot: Tux) -> None:
        """
        Initializes the ErrorHandler cog and stores the bot instance.

        Parameters
        ----------
        bot : Tux
            The running instance of the Tux bot.
        """
        self.bot = bot

        # Stores the original application command error handler so it can be restored
        # when the cog is unloaded. This prevents conflicts if other cogs or the
        # main bot file define their own `tree.on_error`.
        self._old_tree_error = None

    async def cog_load(self) -> None:
        """
        Overrides the bot's application command tree error handler when the cog is loaded.

        This ensures that errors occurring in slash commands are routed to this cog's
        `on_app_command_error` method for centralized processing.
        """
        tree = self.bot.tree
        # Store the potentially existing handler.
        # Using typing.cast for static analysis clarity, assuming the existing handler
        # conforms to the expected AppCommandErrorHandler signature.
        self._old_tree_error = tree.on_error
        # Replace the tree's error handler with this cog's handler.
        tree.on_error = self.on_app_command_error
        logger.debug("Application command error handler mapped.")

    async def cog_unload(self) -> None:
        """
        Restores the original application command tree error handler when the cog is unloaded.

        This is crucial for clean teardown and to avoid interfering with other parts
        of the bot if this cog is dynamically loaded/unloaded.
        """
        if self._old_tree_error:
            # Restore the previously stored handler.
            self.bot.tree.on_error = self._old_tree_error
            logger.debug("Application command error handler restored.")
        else:
            # This might happen if cog_load failed or was never called.
            logger.warning("Application command error handler not restored: No previous handler found.")

    # --- Core Error Processing Logic ---

    async def _handle_error(self, source: ContextOrInteraction, error: Exception) -> None:
        """
        The main internal method for processing any intercepted command error.

        This function performs the following steps:
        1. Unwraps nested errors (like CommandInvokeError, HybridCommandError) to find the root cause.
        2. Checks if the root cause is actually an Exception.
        3. Gathers context information for logging.
        4. Looks up the root error type in `ERROR_CONFIG_MAP` to find handling instructions.
        5. Formats a user-friendly error message based on the configuration.
        6. Creates a standard error embed.
        7. Sends the initial response to the user, handling potential send failures.
        8. Logs the error, reports to Sentry, and attempts to add Event ID to the message.

        Parameters
        ----------
        source : ContextOrInteraction
            The context or interaction object where the error originated.
        error : Exception
            The exception object caught by the listener or tree handler.
        """
        # Step 1: Unwrap nested errors using the helper function.
        root_error = _unwrap_error(error)

        # --- Sentry Transaction Finalization (Added) ---
        self._finish_sentry_transaction_on_error(source, root_error)
        # -----------------------------------------------

        # Step 3: Gather context using the resolved root error.
        error_type: type[Exception] = type(root_error)
        user = self._get_user_from_source(source)
        log_context = self._get_log_context(source, user, root_error)
        log_context["initial_error_type"] = type(error).__name__  # Keep initial error type for context

        # Step 4: Determine handling configuration.
        config = ERROR_CONFIG_MAP.get(error_type)

        # Step 5: Format the user-facing message.
        message = self._get_formatted_message(source, root_error, config)

        # Step 6: Create the error embed.
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            description=message,
        )

        # Step 7: Send response.
        sent_message: discord.Message | None = None
        try:
            sent_message = await self._send_error_response(source, embed)
        except discord.HTTPException as http_exc:
            log_context["send_error"] = str(http_exc)
            logger.bind(**log_context).error("Failed to send error message due to HTTP exception.")
        except Exception as send_exc:
            log_context["send_error"] = str(send_exc)
            log_context["send_error_type"] = type(send_exc).__name__
            logger.bind(**log_context).exception("Unexpected failure during error message sending.")
            self._capture_exception_with_context(
                send_exc,
                log_context,
                "ERROR",
                tags={"failure_point": "send_response"},
            )
            return

        # Step 8 & 9: Log and report.
        sentry_event_id = self._log_and_report_error(root_error, error_type, log_context, config)

        # Step 10: Attempt edit with Sentry ID.
        await self._try_edit_message_with_sentry_id(sent_message, sentry_event_id, log_context)

    @staticmethod
    def _get_user_from_source(source: ContextOrInteraction) -> discord.User | discord.Member:
        """Helper method to consistently extract the user object from either source type."""
        if isinstance(source, discord.Interaction):
            return source.user
        # If not Interaction, it must be Context.
        return source.author

    def _get_log_context(
        self,
        source: ContextOrInteraction,
        user: discord.User | discord.Member,
        error: Exception,
    ) -> dict[str, Any]:
        """
        Builds a dictionary containing structured context information about the error event.

        Includes information about invocation type (prefix/app) and definition type (hybrid/prefix_only/app_only).

        Parameters
        ----------
        source : ContextOrInteraction
            The source of the error.
        user : Union[discord.User, discord.Member]
            The user who triggered the error.
        error : Exception
            The exception that occurred.

        Returns
        -------
        dict[str, Any]
            A dictionary with context keys like user_id, command_name, guild_id, etc.
        """
        context: dict[str, Any] = {
            "user_id": user.id,
            "user_name": str(user),
            "error": str(error),
            "error_type": type(error).__name__,
        }

        # Determine invocation method first using ternary operator
        invoked_via_interaction: bool = (
            True if isinstance(source, discord.Interaction) else source.interaction is not None
        )

        # Set command_type based on invocation method
        context["command_type"] = "app" if invoked_via_interaction else "prefix"
        context["invoked_via_interaction"] = invoked_via_interaction

        # Add specific details based on source type
        if isinstance(source, discord.Interaction):
            context["interaction_id"] = source.id
            context["channel_id"] = source.channel_id
            context["guild_id"] = source.guild_id
            # Determine definition type for app invocation
            if source.command:
                context["command_name"] = source.command.qualified_name
                prefix_command = self.bot.get_command(source.command.qualified_name)
                if prefix_command and isinstance(prefix_command, commands.HybridCommand | commands.HybridGroup):
                    context["command_definition"] = "hybrid"
                else:
                    context["command_definition"] = "app"
            else:
                context["command_definition"] = "unknown"

        else:  # Source is commands.Context
            context["message_id"] = source.message.id
            context["channel_id"] = source.channel.id
            context["guild_id"] = source.guild.id if source.guild else None
            # Determine definition type for prefix invocation
            if source.command:
                context["command_name"] = source.command.qualified_name
                context["command_prefix"] = source.prefix
                context["command_invoked_with"] = source.invoked_with
                if isinstance(source.command, commands.HybridCommand | commands.HybridGroup):
                    context["command_definition"] = "hybrid"
                else:
                    context["command_definition"] = "prefix"
            else:
                context["command_invoked_with"] = source.invoked_with
                context["command_definition"] = "unknown"

        return context

    def _get_formatted_message(
        self,
        source: ContextOrInteraction,
        error: Exception,  # Changed to accept the root error directly
        config: ErrorHandlerConfig | None,
    ) -> str:
        """
        Constructs the final user-facing error message string.

        It retrieves the base format string from the config (or uses the default),
        populates it with basic details ({error}), injects specific details using
        the configured extractor (if any), and includes multiple fallback mechanisms
        to ensure a message is always returned, even if formatting fails.

        Parameters
        ----------
        source : ContextOrInteraction
            The source of the error, used for context in format strings (e.g., {ctx.prefix}).
        error : Exception
            The error object, used for details and the {error} placeholder.
        config : Optional[ErrorHandlerConfig]
            The configuration for this error type.

        Returns
        -------
        str
            The formatted error message ready to be displayed to the user.
        """
        error_type = type(error)
        message_format = config.message_format if config else DEFAULT_ERROR_MESSAGE
        kwargs: dict[str, Any] = {"error": error}

        if isinstance(source, commands.Context):
            kwargs["ctx"] = source
            usage = "(unknown command)"
            if source.command and "{usage}" in message_format:
                usage = source.command.usage or self._generate_default_usage(source.command)
            kwargs["usage"] = usage

        if config and config.detail_extractor:
            try:
                specific_details = config.detail_extractor(error)
                kwargs |= specific_details
            except Exception as ext_exc:
                log_context = self._get_log_context(source, self._get_user_from_source(source), error)
                log_context["extractor_error"] = str(ext_exc)
                logger.bind(**log_context).warning(
                    f"Failed to extract details for {error_type.__name__} using {config.detail_extractor.__name__}",
                )

        # Attempt primary formatting.
        try:
            return message_format.format(**kwargs)
        except Exception as fmt_exc:
            # If primary formatting fails, use the fallback helper.
            log_context = self._get_log_context(source, self._get_user_from_source(source), error)
            log_context["format_error"] = str(fmt_exc)
            logger.bind(**log_context).warning(
                f"Failed to format error message for {error_type.__name__}. Using fallback.",
            )
            # Use the new fallback helper function
            return _fallback_format_message(message_format, error)

    @staticmethod
    def _generate_default_usage(command: commands.Command[Any, ..., Any]) -> str:
        """
        Generates a basic usage string for a traditional command based on its signature.

        Used as a fallback when a command doesn't have a specific `usage` attribute defined.

        Parameters
        ----------
        command : commands.Command
            The command object.

        Returns
        -------
        str
            A usage string like "command_name [required_arg] <optional_arg>".
        """
        signature = command.signature.strip()
        # Combine name and signature, adding a space only if a signature exists.
        return f"{command.qualified_name}{f' {signature}' if signature else ''}"

    async def _send_error_response(self, source: ContextOrInteraction, embed: discord.Embed) -> discord.Message | None:
        """
        Sends the generated error embed to the user via the appropriate channel/method.

        - For Interactions: Uses ephemeral messages (either initial response or followup).
        - For Context: Uses `reply` with `delete_after` for cleanup.

        Returns the sent message object if it was a reply (editable), otherwise None.

        Parameters
        ----------
        source : ContextOrInteraction
            The source defining where and how to send the message.
        embed : discord.Embed
            The error embed to send.

        Returns
        -------
        Optional[discord.Message]
            The sent message object if sent via context reply, otherwise None.
        """
        if isinstance(source, discord.Interaction):
            # Send ephemeral message for Application Commands.
            # This keeps the channel clean and respects user privacy.
            if source.response.is_done():
                # If the initial interaction response (`defer` or `send_message`) was already sent.
                await source.followup.send(embed=embed, ephemeral=True)
            else:
                # If this is the first response to the interaction.
                await source.response.send_message(embed=embed, ephemeral=True)
            return None  # Ephemeral messages cannot be reliably edited later

        # Send reply for Traditional Commands.
        # `ephemeral` is not available for context-based replies.
        # Use `delete_after` to automatically remove the error message.
        # Directly return the result of the reply await.
        return await source.reply(
            embed=embed,
            delete_after=COMMAND_ERROR_DELETE_AFTER,
            mention_author=False,  # Avoid potentially annoying pings for errors.
        )

    # --- Sentry Transaction Finalization Logic (Added) ---
    def _finish_sentry_transaction_on_error(self, source: ContextOrInteraction, root_error: Exception) -> None:
        """Attempts to find and finish an active Sentry transaction based on the error source."""
        if not sentry_sdk.is_initialized():
            return

        transaction: Any | None = None
        transaction_id: int | None = None
        command_type: str | None = None

        # Status mapping dictionaries
        app_command_status_map = {
            app_commands.CommandNotFound: SENTRY_STATUS_NOT_FOUND,
            app_commands.CheckFailure: SENTRY_STATUS_PERMISSION_DENIED,
            app_commands.TransformerError: SENTRY_STATUS_INVALID_ARGUMENT,
        }

        prefix_command_status_map = {
            commands.CommandNotFound: SENTRY_STATUS_NOT_FOUND,
            commands.UserInputError: SENTRY_STATUS_INVALID_ARGUMENT,
            commands.CheckFailure: SENTRY_STATUS_PERMISSION_DENIED,
            commands.CommandOnCooldown: SENTRY_STATUS_RESOURCE_EXHAUSTED,
            commands.MaxConcurrencyReached: SENTRY_STATUS_RESOURCE_EXHAUSTED,
        }

        # Default status
        status: str = SENTRY_STATUS_INTERNAL_ERROR

        try:
            # Determine ID and type based on source
            if isinstance(source, discord.Interaction):
                transaction_id = source.id
                command_type = "app_command"

                # Lookup status in mapping
                for error_type, error_status in app_command_status_map.items():
                    if isinstance(root_error, error_type):
                        status = error_status
                        break

            elif isinstance(source, commands.Context):  # type: ignore
                transaction_id = source.message.id
                command_type = "prefix_command"

                # Lookup status in mapping
                for error_type, error_status in prefix_command_status_map.items():
                    if isinstance(root_error, error_type):
                        status = error_status
                        break

            else:
                logger.warning(f"Unknown error source type encountered: {type(source).__name__}")
                return  # Cannot determine transaction ID

            # Try to pop the transaction from the bot's central store
            if transaction_id is not None:  # type: ignore
                transaction = self.bot.active_sentry_transactions.pop(transaction_id, None)

            if transaction:
                transaction.set_status(status)
                transaction.finish()
                logger.trace(
                    f"Finished Sentry transaction ({status}) for errored {command_type} (ID: {transaction_id})",
                )

        except Exception as e:
            logger.exception(f"Error during Sentry transaction finalization for ID {transaction_id}: {e}")
            # Capture this specific failure to Sentry if needed
            sentry_sdk.capture_exception(e, hint={"context": "Sentry transaction finalization"})

    # --- Sentry Reporting Logic ---

    @staticmethod
    def _capture_exception_with_context(
        error: Exception,
        log_context: dict[str, Any],
        level: str = "ERROR",
        tags: dict[str, str] | None = None,
    ) -> str | None:
        """
        Safely sends an exception to Sentry, enriching it with structured context.

        This method pushes a new scope to Sentry, adds user information, the detailed
        log context, the specified logging level, and any custom tags before capturing
        the exception. It includes error handling to prevent Sentry SDK issues from
        crashing the error handler itself.

        Parameters
        ----------
        error : Exception
            The exception to report.
        log_context : dict[str, Any]
            The dictionary of context information gathered by `_get_log_context`.
        level : str, optional
            The severity level for the Sentry event ('info', 'warning', 'error', etc.). Defaults to "ERROR".
        tags : Optional[dict[str, str]], optional
            Additional key-value tags to attach to the Sentry event. Defaults to None.

        Returns
        -------
        Optional[str]
            The Sentry event ID if capture was successful, otherwise None.
        """
        event_id: str | None = None
        try:
            # Create an isolated scope for this Sentry event.
            with sentry_sdk.push_scope() as scope:
                # Add user identification.
                scope.set_user({"id": log_context.get("user_id"), "username": log_context.get("user_name")})
                # Attach the detailed context dictionary under the 'discord' key.
                scope.set_context("discord", log_context)
                # Set the severity level of the event.
                scope.level = level.lower()

                # --- Add specific tags for better filtering/searching --- #
                scope.set_tag("command_name", log_context.get("command_name", "Unknown"))
                scope.set_tag("command_type", log_context.get("command_type", "Unknown"))
                scope.set_tag("command_definition", log_context.get("command_definition", "Unknown"))

                # Add new tag for interaction check
                scope.set_tag("invoked_via_interaction", str(log_context.get("invoked_via_interaction", False)).lower())

                # Handle potential None for guild_id (e.g., in DMs)
                guild_id = log_context.get("guild_id")
                scope.set_tag("guild_id", str(guild_id) if guild_id else "DM")

                # Add any custom tags provided when calling this function.
                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)

                # Send the exception event to Sentry and capture the returned event ID.
                event_id = sentry_sdk.capture_exception(error)

                # Debug log indicating successful reporting.
                if event_id:
                    logger.debug(f"Reported {type(error).__name__} to Sentry ({event_id})")
                else:
                    logger.warning(f"Captured {type(error).__name__} but Sentry returned no ID.")

        except Exception as sentry_exc:
            # Log if reporting to Sentry fails, but don't let it stop the error handler.
            logger.error(f"Failed to report {type(error).__name__} to Sentry: {sentry_exc}")

        return event_id  # Return the event ID (or None if capture failed)

    def _log_and_report_error(
        self,
        root_error: Exception,
        error_type: type[Exception],
        log_context: dict[str, Any],
        config: ErrorHandlerConfig | None,
    ) -> str | None:
        """Handles logging the error and reporting it to Sentry based on config."""
        sentry_event_id: str | None = None
        if config:
            # Log handled errors according to their configured level.
            logger.bind(**log_context).log(config.log_level, f"Handled expected error: {error_type.__name__}")
            if config.send_to_sentry:
                # Optionally send handled errors to Sentry.
                sentry_event_id = self._capture_exception_with_context(
                    root_error,
                    log_context,
                    config.log_level,
                    tags={"error_type": "handled"},
                )
        else:
            # Log unhandled errors at ERROR level and always report to Sentry.
            logger.bind(**log_context).error(f"Unhandled error: {error_type.__name__}")
            sentry_event_id = self._log_and_capture_unhandled(root_error, log_context)
        return sentry_event_id

    async def _try_edit_message_with_sentry_id(
        self,
        sent_message: discord.Message | None,
        sentry_event_id: str | None,
        log_context: dict[str, Any],  # Pass context for logging edit failures
    ) -> None:
        """Attempts to edit the sent message embed to include the Sentry event ID."""
        if not sentry_event_id or not sent_message:
            return  # Nothing to add or no message to edit

        try:
            # Fetch the message again to ensure it exists and reduce race conditions.
            fetched_message = await sent_message.channel.fetch_message(sent_message.id)

            if not fetched_message.embeds:
                logger.bind(**log_context).warning(
                    f"Could not add Sentry ID {sentry_event_id} to message {sent_message.id}: No embeds found.",
                )
                return

            # --- Modify Description instead of Footer --- #
            original_embed = fetched_message.embeds[0]
            # Use Discord's Subtext markdown format
            sentry_id_text = f"\n-# Error ID: {sentry_event_id}"
            new_description = (original_embed.description or "") + sentry_id_text

            # Check length limit (4096 chars for embed description)
            if len(new_description) > 4096:
                logger.bind(**log_context).warning(
                    f"Could not add Sentry ID {sentry_event_id} to message {sent_message.id}: New description would exceed 4096 characters.",
                )
                return  # Don't attempt edit if it will fail due to length

            original_embed.description = new_description
            # -------------------------------------------- #

            # Edit the message.
            await fetched_message.edit(embed=original_embed)

        except discord.NotFound:
            logger.bind(**log_context).warning(
                f"Could not add Sentry ID {sentry_event_id}: Original message {sent_message.id} not found (likely deleted).",
            )
        except discord.Forbidden:
            logger.bind(**log_context).warning(
                f"Could not add Sentry ID {sentry_event_id}: Missing permissions to edit message {sent_message.id}.",
            )
        except discord.HTTPException as edit_exc:
            # Log potential length errors here too, although checked above
            logger.bind(**log_context).error(
                f"Failed to edit message {sent_message.id} with Sentry ID {sentry_event_id}: {edit_exc}",
            )
        except Exception as unexpected_edit_exc:
            logger.bind(**log_context).exception(
                f"Unexpected error editing message {sent_message.id} with Sentry ID {sentry_event_id}",
                exc_info=unexpected_edit_exc,
            )

    def _log_and_capture_unhandled(self, error: Exception, log_context: dict[str, Any]) -> str | None:
        """
        Handles errors not found in the `ERROR_CONFIG_MAP`.

        It logs the error with its full traceback at the ERROR level and reports
        it to Sentry, tagging it as 'unhandled'.

        Parameters
        ----------
        error : Exception
            The unhandled exception.
        log_context : dict[str, Any]
            The context dictionary for logging and reporting.

        Returns
        -------
        Optional[str]
            The Sentry event ID if capture was successful, otherwise None.
        """
        # Generate the formatted traceback string.
        trace = traceback.format_exception(type(error), error, error.__traceback__)
        formatted_trace = "".join(trace)

        # Log the error locally with full traceback and context.
        logger.bind(**log_context).error(f"Unhandled Error: {error}\nTraceback:\n{formatted_trace}")

        # Report the unhandled error to Sentry with high severity.
        # Directly return the result from _capture_exception_with_context.
        return self._capture_exception_with_context(error, log_context, "ERROR", tags={"error_type": "unhandled"})

    # --- Command Suggestion Logic ---

    async def _suggest_command(self, ctx: commands.Context[Tux]) -> list[str] | None:
        """
        Attempts to find similar command names when a CommandNotFound error occurs.

        Uses the Levenshtein distance algorithm to compare the invoked command name
        against all registered command names and aliases. Returns a list of the
        closest matches within configured distance thresholds.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object from the failed command invocation.

        Returns
        -------
        Optional[List[str]]
            A list of suggested command qualified names (e.g., ["tag create", "tag edit"])
            or None if no suitable suggestions are found.
        """
        # Suggestions require a guild context (commands vary across guilds)
        # and the name the user actually typed.
        if not ctx.guild or not ctx.invoked_with:
            return None

        command_name = ctx.invoked_with
        # Create log context specific to this suggestion attempt.
        # Using a dummy CommandNotFound for context consistency.
        log_context = self._get_log_context(ctx, ctx.author, commands.CommandNotFound())
        log_context["suggest_input"] = command_name

        # Use stricter distance/count limits for very short command names
        # to avoid overly broad or irrelevant suggestions.
        is_short = len(command_name) <= SHORT_CMD_LEN_THRESHOLD
        max_suggestions = SHORT_CMD_MAX_SUGGESTIONS if is_short else DEFAULT_MAX_SUGGESTIONS
        max_distance = SHORT_CMD_MAX_DISTANCE if is_short else DEFAULT_MAX_DISTANCE_THRESHOLD
        log_context["suggest_max_dist"] = max_distance
        log_context["suggest_max_count"] = max_suggestions

        logger.bind(**log_context).debug("Attempting command suggestion.")

        # Store potential matches: {qualified_name: min_distance}
        command_distances: dict[str, int] = {}

        # Iterate through all commands registered with the bot.
        for cmd in self.bot.walk_commands():
            # Do not suggest hidden commands.
            if cmd.hidden:
                continue

            min_dist_for_cmd = max_distance + 1
            qualified_name = cmd.qualified_name
            # Check against the command's main name and all its aliases.
            names_to_check = [qualified_name, *cmd.aliases]

            # Find the minimum distance between the user's input and any of the command's names.
            for name in names_to_check:
                # Perform case-insensitive comparison.
                distance = Levenshtein.distance(command_name.lower(), name.lower())
                min_dist_for_cmd = min(min_dist_for_cmd, distance)

            # If the command is close enough, store its distance.
            if min_dist_for_cmd <= max_distance:
                # If we found a closer match for this command (e.g., via an alias)
                # than previously stored, update the distance.
                current_min = command_distances.get(qualified_name, max_distance + 1)
                if min_dist_for_cmd < current_min:
                    command_distances[qualified_name] = min_dist_for_cmd

        # If no commands were within the distance threshold.
        if not command_distances:
            logger.bind(**log_context).debug("No close command matches found for suggestion.")
            return None

        # Sort the found commands by distance (closest first).
        sorted_suggestions = sorted(command_distances.items(), key=lambda item: item[1])

        # Take the top N suggestions based on the configured limit.
        final_suggestions = [cmd_name for cmd_name, _ in sorted_suggestions[:max_suggestions]]

        log_context["suggestions_found"] = final_suggestions
        logger.bind(**log_context).debug("Command suggestions generated.")
        # Return the list of names, or None if the list is empty (shouldn't happen here, but safety check).
        return final_suggestions or None

    async def _handle_command_not_found(self, ctx: commands.Context[Tux]) -> None:
        """
        Specific handler for the `CommandNotFound` error.

        It calls `_suggest_command` to get potential alternatives and sends
        a user-friendly message containing these suggestions if any are found.
        It avoids sending a generic "Command not found" message if no suggestions
        are available to reduce channel noise.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context where the CommandNotFound error occurred.
        """
        suggestions = await self._suggest_command(ctx)

        # Create log context specific to this CommandNotFound event.
        log_context = self._get_log_context(ctx, ctx.author, commands.CommandNotFound())

        if suggestions:
            # Format the suggestions list for display.
            formatted_suggestions = ", ".join(f"`{ctx.prefix}{s}`" for s in suggestions)
            message = f"Command `{ctx.invoked_with}` not found. Did you mean: {formatted_suggestions}?"

            # Create an informational embed for the suggestions.
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.INFO,
                description=message,
            )
            try:
                # Send the suggestion message, automatically deleting it after a short period.
                await ctx.send(embed=embed, delete_after=SUGGESTION_DELETE_AFTER)
                log_context["suggestions_sent"] = suggestions
                logger.bind(**log_context).info("Sent command suggestions.")
            except discord.HTTPException as e:
                # Log if sending the suggestion message fails.
                log_context["send_error"] = str(e)
                logger.bind(**log_context).error("Failed to send command suggestion message due to HTTP exception.")
            except Exception as send_exc:
                # Log any other unexpected error during suggestion sending.
                log_context["send_error"] = str(send_exc)
                log_context["send_error_type"] = type(send_exc).__name__
                logger.bind(**log_context).exception("Unexpected failure sending command suggestions.")
        else:
            # Log that the command wasn't found and no suitable suggestions were generated.
            # No message is sent back to the user in this case to avoid unnecessary noise.
            logger.bind(**log_context).info("Command not found, no suggestions generated.")

    # --- Discord Event Listeners ---

    @commands.Cog.listener("on_command_error")
    async def on_command_error_listener(self, ctx: commands.Context[Tux], error: commands.CommandError) -> None:
        """
        The primary listener for errors occurring in traditional (prefix) commands.

        It performs the following checks:

        - If the error is `CommandNotFound`, delegates to `_handle_command_not_found`.
        - If the command itself has a local error handler (`@command.error`), ignores the error.
        - If the command's cog has a local error handler (`Cog.listener('on_cog_command_error')`),ignores the error (unless it's this ErrorHandler cog itself).
        - Otherwise, delegates the error to the central `_handle_error` method.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context where the error occurred.
        error : commands.CommandError
            The error that was raised.
        """
        # Gather initial context for logging purposes.
        log_context = self._get_log_context(ctx, ctx.author, error)

        # Handle CommandNotFound separately to provide suggestions.
        if isinstance(error, commands.CommandNotFound):
            await self._handle_command_not_found(ctx)
            # Stop further processing for CommandNotFound.
            return

        # Check for and respect local error handlers on the command itself.
        if ctx.command and ctx.command.has_error_handler():
            logger.bind(**log_context).debug(
                f"Command '{ctx.command.qualified_name}' has a local error handler. Skipping global handler.",
            )
            return

        # Check for and respect local error handlers on the command's cog,
        # ensuring we don't bypass the global handler if the error originated *within* this cog.
        if ctx.cog and ctx.cog.has_error_handler() and ctx.cog is not self:
            logger.bind(**log_context).debug(
                f"Cog '{ctx.cog.qualified_name}' has a local error handler. Skipping global handler.",
            )
            return

        # If no local handlers intercepted the error, process it globally.
        log_context = self._get_log_context(ctx, ctx.author, error)  # Regenerate context *after* CommandNotFound check
        await self._handle_error(ctx, error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction[Tux],
        error: app_commands.AppCommandError,
    ) -> None:
        """
        The error handler for application (slash) commands, registered via `tree.on_error`.

        Unlike prefix commands, checking for local handlers on app commands is less
        straightforward via the interaction object alone. This handler assumes that if an
        error reaches here, it should be processed globally. It delegates all errors
        directly to the central `_handle_error` method.

        Parameters
        ----------
        interaction : discord.Interaction[Tux]
            The interaction where the error occurred.
        error : app_commands.AppCommandError
            The error that was raised.
        """
        # Gather context for logging.
        log_context = self._get_log_context(interaction, interaction.user, error)

        # Currently, there's no reliable public API on the interaction object to check
        # if the specific AppCommand has a local @error handler attached.
        # Therefore, we assume errors reaching this global tree handler should be processed.
        # If cog-level app command error handling is desired, it typically needs to be
        # implemented within the cog itself using try/except blocks or decorators that
        # register their own error handlers on the commands they define.

        # Delegate all app command errors to the central handler.
        logger.bind(**log_context).debug(f"Handling app command error via global handler: {type(error).__name__}")
        await self._handle_error(interaction, error)


async def setup(bot: Tux) -> None:
    """Standard setup function to add the ErrorHandler cog to the bot."""
    logger.debug("Setting up ErrorHandler")
    await bot.add_cog(ErrorHandler(bot))
