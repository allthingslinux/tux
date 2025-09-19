"""Error handling mixin for common error patterns in cogs and services."""

from typing import Any

from loguru import logger

from tux.shared.error_utils import log_and_capture_error
from tux.shared.exceptions import TuxError


class ErrorHandlerMixin:
    """Mixin providing common error handling methods for cogs and services."""

    def handle_error(
        self,
        error: Exception,
        operation: str,
        *,
        log_level: str = "error",
        context: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> str:
        """Handle an error with consistent logging and Sentry capture.

        Args:
            error: The exception that occurred
            operation: Name of the operation that failed
            log_level: Log level to use
            context: Additional context for Sentry
            user_message: Custom user-friendly message

        Returns:
            User-friendly error message
        """
        # Log and capture the error
        log_and_capture_error(
            error,
            operation,
            log_level=log_level,
            context=context,
            tags={"component": getattr(self, "__class__", {}).get("__name__", "unknown")},
        )

        # Return user-friendly message
        if user_message:
            return user_message
        if isinstance(error, TuxError):
            return str(error)
        return "An unexpected error occurred. Please try again later."

    def log_warning(self, message: str, **context: Any) -> None:
        """Log a warning with optional context."""
        if context:
            logger.bind(**context).warning(message)
        else:
            logger.warning(message)

    def log_info(self, message: str, **context: Any) -> None:
        """Log an info message with optional context."""
        if context:
            logger.bind(**context).info(message)
        else:
            logger.info(message)

    def log_debug(self, message: str, **context: Any) -> None:
        """Log a debug message with optional context."""
        if context:
            logger.bind(**context).debug(message)
        else:
            logger.debug(message)
