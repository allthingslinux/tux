"""Unified Sentry integration utilities for consistent error reporting."""

from typing import Any, Literal

import sentry_sdk
from loguru import logger

from tux.shared.exceptions import TuxError

# Type alias for Sentry log levels
LogLevelStr = Literal["fatal", "critical", "error", "warning", "info", "debug"]


def capture_exception_safe(exception: Exception) -> None:
    """Safely capture an exception to Sentry if initialized.

    This replaces the function from tracing.py to centralize Sentry utilities.

    Args:
        exception: The exception to report
    """
    if sentry_sdk.is_initialized():
        sentry_sdk.capture_exception(exception)


def capture_message_safe(message: str, level: LogLevelStr = "info") -> None:
    """Safely capture a message to Sentry if initialized.

    Args:
        message: The message to capture
        level: Sentry level (error, warning, info, debug)
    """
    if sentry_sdk.is_initialized():
        sentry_sdk.capture_message(message, level=level)


def capture_tux_exception(
    exception: Exception,
    *,
    context: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
    level: str = "error",
) -> None:
    """Capture an exception with Tux-specific context.

    Args:
        exception: The exception to capture
        context: Additional context data
        tags: Tags to add to the event
        level: Sentry level (error, warning, info, debug)
    """
    try:
        # Set Tux-specific context
        with sentry_sdk.push_scope() as scope:
            # Add exception type information
            scope.set_tag("tux.exception_type", type(exception).__name__)
            scope.set_tag("tux.is_tux_error", isinstance(exception, TuxError))

            # Add custom context
            if context:
                scope.set_context("tux_context", context)

            # Add custom tags
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)

            # Set level
            scope.level = level

            # Capture the exception
            sentry_sdk.capture_exception(exception)

    except Exception as e:
        # Fallback logging if Sentry fails
        logger.error(f"Failed to capture exception to Sentry: {e}")
        logger.exception(f"Original exception: {exception}")


def capture_database_error(
    exception: Exception,
    *,
    operation: str | None = None,
    table: str | None = None,
) -> None:
    """Capture a database-related error with relevant context.

    Args:
        exception: The database exception
        operation: The database operation that failed
        table: The table involved in the operation
    """
    context: dict[str, Any] = {}
    if operation:
        context["operation"] = operation
    if table:
        context["table"] = table

    capture_tux_exception(
        exception,
        context=context,
        tags={"component": "database"},
    )


def capture_cog_error(
    exception: Exception,
    *,
    cog_name: str | None = None,
    command_name: str | None = None,
) -> None:
    """Capture a cog-related error with relevant context.

    Args:
        exception: The cog exception
        cog_name: The name of the cog
        command_name: The name of the command
    """
    context: dict[str, Any] = {}
    if cog_name:
        context["cog_name"] = cog_name
    if command_name:
        context["command_name"] = command_name

    capture_tux_exception(
        exception,
        context=context,
        tags={"component": "cog"},
    )


def capture_api_error(
    exception: Exception,
    *,
    service_name: str | None = None,
    endpoint: str | None = None,
    status_code: int | None = None,
) -> None:
    """Capture an API-related error with relevant context.

    Args:
        exception: The API exception
        service_name: The name of the external service
        endpoint: The API endpoint that failed
        status_code: The HTTP status code
    """
    context: dict[str, Any] = {}
    if service_name:
        context["service_name"] = service_name
    if endpoint:
        context["endpoint"] = endpoint
    if status_code:
        context["status_code"] = status_code

    capture_tux_exception(
        exception,
        context=context,
        tags={"component": "api"},
    )


def set_user_context(user_id: int, username: str | None = None) -> None:
    """Set user context for Sentry events.

    Args:
        user_id: Discord user ID
        username: Discord username
    """
    try:
        sentry_sdk.set_user(
            {
                "id": str(user_id),
                "username": username,
            },
        )
    except Exception as e:
        logger.debug(f"Failed to set Sentry user context: {e}")


def set_guild_context(guild_id: int, guild_name: str | None = None) -> None:
    """Set guild context for Sentry events.

    Args:
        guild_id: Discord guild ID
        guild_name: Discord guild name
    """
    try:
        sentry_sdk.set_context(
            "guild",
            {
                "id": str(guild_id),
                "name": guild_name,
            },
        )
    except Exception as e:
        logger.debug(f"Failed to set Sentry guild context: {e}")


def set_command_context(command_name: str, cog_name: str | None = None) -> None:
    """Set command context for Sentry events.

    Args:
        command_name: Name of the command being executed
        cog_name: Name of the cog containing the command
    """
    try:
        context = {"command": command_name}
        if cog_name:
            context["cog"] = cog_name

        sentry_sdk.set_context("command", context)
    except Exception as e:
        logger.debug(f"Failed to set Sentry command context: {e}")
