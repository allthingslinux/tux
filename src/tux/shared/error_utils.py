"""Utility functions for error handling and logging."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from loguru import logger

from tux.services.sentry import capture_exception_safe, capture_tux_exception
from tux.shared.exceptions import TuxError

T = TypeVar("T")


def log_and_capture(
    error: Exception,
    *,
    operation: str = "operation",
    log_level: str = "error",
    context: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Log an error and capture it to Sentry with consistent formatting."""
    getattr(logger, log_level)(f"❌ {operation} failed: {error}")
    if isinstance(error, TuxError):
        capture_tux_exception(error)
    else:
        capture_exception_safe(error)


def safe_operation(
    operation_name: str,
    operation: Callable[[], T],
    *,
    fallback_value: T | None = None,
    log_level: str = "error",
    capture_sentry: bool = True,
    context: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> T | None:
    """Execute an operation safely with error handling."""
    try:
        return operation()
    except Exception as e:
        getattr(logger, log_level)(f"❌ {operation_name} failed: {e}")
        if capture_sentry:
            if isinstance(e, TuxError):
                capture_tux_exception(e)
            else:
                capture_exception_safe(e)
        return fallback_value


async def safe_async_operation(
    operation_name: str,
    operation: Callable[[], Any],
    *,
    fallback_value: Any = None,
    log_level: str = "error",
    capture_sentry: bool = True,
    context: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> Any:
    """Execute an async operation safely with error handling."""
    try:
        return await operation()
    except Exception as e:
        getattr(logger, log_level)(f"❌ {operation_name} failed: {e}")
        if capture_sentry:
            if isinstance(e, TuxError):
                capture_tux_exception(e)
            else:
                capture_exception_safe(e)
        return fallback_value


def format_error_for_user(error: Exception) -> str:
    """Format an error message for user display."""
    if isinstance(error, TuxError):
        return str(error)
    return "An unexpected error occurred. Please try again later."
