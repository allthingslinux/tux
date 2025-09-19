"""Centralized error handling utilities to reduce duplication."""

import traceback
from collections.abc import Callable
from typing import Any, TypeVar

from loguru import logger

from tux.shared.exceptions import TuxError
from tux.shared.sentry_utils import capture_tux_exception

T = TypeVar("T")


def log_and_capture_error(
    error: Exception,
    operation: str,
    *,
    log_level: str = "error",
    context: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Log an error and capture it to Sentry with consistent formatting."""
    getattr(logger, log_level)(f"❌ {operation} failed: {error}")
    capture_tux_exception(
        error,
        context={**(context or {}), "operation": operation},
        tags={**(tags or {}), "error_handler": "log_and_capture"},
    )


def safe_operation(
    operation_name: str,
    operation: Callable[[], T],
    *,
    fallback_value: T | None = None,
    log_level: str = "error",
    capture_sentry: bool = True,
    context: dict[str, Any] | None = None,
) -> T | None:
    """Execute an operation safely with error handling."""
    try:
        return operation()
    except Exception as e:
        getattr(logger, log_level)(f"❌ {operation_name} failed: {e}")
        if capture_sentry:
            capture_tux_exception(
                e,
                context={**(context or {}), "operation": operation_name},
                tags={"error_handler": "safe_operation"},
            )
        return fallback_value


async def safe_async_operation(
    operation_name: str,
    operation: Callable[[], Any],
    *,
    fallback_value: Any = None,
    log_level: str = "error",
    capture_sentry: bool = True,
    context: dict[str, Any] | None = None,
) -> Any:
    """Execute an async operation safely with error handling."""
    try:
        return await operation()
    except Exception as e:
        getattr(logger, log_level)(f"❌ {operation_name} failed: {e}")
        if capture_sentry:
            capture_tux_exception(
                e,
                context={**(context or {}), "operation": operation_name},
                tags={"error_handler": "safe_async_operation"},
            )
        return fallback_value


def format_error_for_user(error: Exception) -> str:
    """Format an error message for user display."""
    if isinstance(error, TuxError):
        return str(error)
    return "An unexpected error occurred. Please try again later."


def get_error_context(error: Exception) -> dict[str, Any]:
    """Extract context information from an error."""
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "is_tux_error": isinstance(error, TuxError),
        "traceback": traceback.format_exc(),
    }
