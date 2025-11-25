"""Sentry utility functions for specialized error reporting."""

from __future__ import annotations

import inspect
from typing import Any

import httpx
import sentry_sdk
from loguru import logger

from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIPermissionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
    TuxError,
)

from .config import is_initialized


def capture_exception_safe(
    error: Exception,
    *,
    extra_context: dict[str, Any] | None = None,
    capture_locals: bool = False,
) -> None:
    """Safely capture an exception with optional context and locals."""
    if not is_initialized():
        logger.error(f"Sentry not initialized, logging error: {error}")
        return

    try:
        with sentry_sdk.push_scope() as scope:
            if extra_context:
                scope.set_context("extra", extra_context)

            if capture_locals:
                # Capture local variables from the calling frame
                frame = inspect.currentframe()
                if frame and frame.f_back:
                    caller_frame = frame.f_back
                    scope.set_context("locals", dict(caller_frame.f_locals))

            scope.set_tag("error.captured_safely", True)
            sentry_sdk.capture_exception(error)
    except Exception as capture_error:
        logger.error(f"Failed to capture exception in Sentry: {capture_error}")


def capture_tux_exception(
    error: TuxError,
    *,
    command_name: str | None = None,
    user_id: str | None = None,
    guild_id: str | None = None,
) -> None:
    """Capture a TuxError with specialized context."""
    if not is_initialized():
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error.type", "tux_error")
        scope.set_tag("error.severity", getattr(error, "severity", "unknown"))

        tux_context = {
            "error_code": getattr(error, "code", None),
            "user_facing": getattr(error, "user_facing", False),
        }

        if command_name:
            tux_context["command"] = command_name
        if user_id:
            tux_context["user_id"] = user_id
        if guild_id:
            tux_context["guild_id"] = guild_id

        scope.set_context("tux_error", tux_context)
        sentry_sdk.capture_exception(error)


def capture_database_error(
    error: Exception,
    *,
    query: str | None = None,
    table: str | None = None,
    operation: str | None = None,
) -> None:
    """Capture a database-related error with context."""
    if not is_initialized():
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error.type", "database")

        db_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        if query:
            db_context["query"] = query
        if table:
            db_context["table"] = table
        if operation:
            db_context["operation"] = operation

        scope.set_context("database", db_context)
        sentry_sdk.capture_exception(error)


def capture_cog_error(
    error: Exception,
    *,
    cog_name: str,
    command_name: str | None = None,
    event_name: str | None = None,
) -> None:
    """Capture a cog-related error with context."""
    if not is_initialized():
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error.type", "cog")
        scope.set_tag("cog.name", cog_name)

        cog_context = {
            "cog_name": cog_name,
            "error_type": type(error).__name__,
        }

        if command_name:
            cog_context["command"] = command_name
            scope.set_tag("command.name", command_name)
        if event_name:
            cog_context["event"] = event_name
            scope.set_tag("event.name", event_name)

        scope.set_context("cog_error", cog_context)
        sentry_sdk.capture_exception(error)


def capture_api_error(
    error: Exception,
    *,
    endpoint: str | None = None,
    status_code: int | None = None,
    response_data: dict[str, Any] | None = None,
) -> None:
    """Capture an API-related error with context."""
    if not is_initialized():
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error.type", "api")

        api_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        if endpoint:
            api_context["endpoint"] = endpoint
            scope.set_tag("api.endpoint", endpoint)
        if status_code:
            api_context["status_code"] = str(status_code)
            scope.set_tag("api.status_code", status_code)
        if response_data:
            api_context["response"] = str(response_data)

        scope.set_context("api_error", api_context)
        sentry_sdk.capture_exception(error)


def convert_httpx_error(
    error: Exception,
    service_name: str,
    endpoint: str,
    *,
    not_found_resource: str | None = None,
) -> None:
    """
    Convert HTTPX error to TuxAPI exception and report to Sentry.

    This function eliminates the duplicated error handling logic that's
    currently repeated 20+ times across API wrappers (github.py, wandbox.py, etc.).

    Parameters
    ----------
    error : Exception
        The HTTPX error to convert.
    service_name : str
        Name of the API service (e.g., "GitHub", "Wikipedia", "Wandbox").
    endpoint : str
        API endpoint identifier (e.g., "repos.get", "issues.create").
    not_found_resource : str | None, optional
        Resource identifier for 404 errors (e.g., "Issue #123", "repo/name").
        If not provided, defaults to "resource".

    Raises
    ------
    TuxAPIResourceNotFoundError
        For 404 errors (resource not found).
    TuxAPIPermissionError
        For 403 errors (permission denied).
    TuxAPIRequestError
        For other HTTP status errors (4xx, 5xx).
    TuxAPIConnectionError
        For connection/request errors (network issues, timeouts).
    """
    logger.error(f"API error in {endpoint} ({service_name}): {error}")

    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code

        # Handle 404 Not Found
        if status_code == 404:
            resource = not_found_resource or "resource"
            raise TuxAPIResourceNotFoundError(
                service_name=service_name,
                resource_identifier=resource,
            ) from error

        # Handle 403 Forbidden
        if status_code == 403:
            raise TuxAPIPermissionError(service_name=service_name) from error

        # Handle other status errors - use existing capture_api_error()
        capture_api_error(error, endpoint=endpoint, status_code=status_code)
        raise TuxAPIRequestError(
            service_name=service_name,
            status_code=status_code,
            reason=error.response.text,
        ) from error

    # Handle connection/request errors
    if isinstance(error, httpx.RequestError):
        capture_api_error(error, endpoint=endpoint)
        raise TuxAPIConnectionError(
            service_name=service_name,
            original_error=error,
        ) from error

    # Handle other unexpected errors
    capture_api_error(error, endpoint=endpoint)
    raise error
