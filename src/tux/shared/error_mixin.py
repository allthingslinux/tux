"""Error handling mixin for common error patterns in cogs and services."""

from typing import Any

from loguru import logger

from tux.services.sentry import capture_exception_safe, capture_tux_exception, set_context, set_tag
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

        Returns
        -------
            User-friendly error message
        """
        # Log the error
        getattr(logger, log_level)(f"❌ {operation} failed: {error}")

        # Set Sentry context and tags
        if context:
            set_context("operation_context", context)

        set_tag("component", getattr(self.__class__, "__name__", "unknown"))
        set_tag("operation", operation)

        # Capture to Sentry with appropriate function
        if isinstance(error, TuxError):
            capture_tux_exception(error)
        else:
            capture_exception_safe(error)

        # Return user-friendly message
        if user_message:
            return user_message
        if isinstance(error, TuxError):
            return str(error)
        return "An unexpected error occurred. Please try again later."
