"""
Sentry Integration Manager.

This module provides the `SentryManager` class, a centralized wrapper for all
interactions with the Sentry SDK. Its primary responsibilities include:

- **Initialization**: Configuring and initializing the Sentry SDK with the
  appropriate DSN, release version, and environment settings.
- **Graceful Shutdown**: Handling OS signals (SIGTERM, SIGINT) to ensure that
  all pending Sentry events are flushed before the application exits.
- **Context Management**: Providing methods to enrich Sentry events with
  contextual data, such as user information, command details, and custom tags.
- **Event Capturing**: Offering a simplified interface (`capture_exception`,
  `capture_message`) for sending events to Sentry.
"""

from __future__ import annotations

from typing import Any, Literal

import discord
import sentry_sdk
from discord import Interaction
from discord.ext import commands
from loguru import logger

from .config import flush, flush_async, is_initialized, report_signal, setup
from .context import (
    set_command_context,
    set_context,
    set_tag,
    set_user_context,
    track_command_end,
    track_command_start,
)
from .tracing import (
    DummySpan,
    DummyTransaction,
    add_breadcrumb,
    capture_span_exception,
    enhanced_span,
    finish_transaction_on_error,
    get_current_span,
    instrument_bot_commands,
    safe_set_name,
    set_setup_phase_tag,
    set_span_attributes,
    span,
    start_span,
    start_transaction,
    transaction,
)

# Type alias for Sentry's log level strings.
LogLevelStr = Literal["fatal", "critical", "error", "warning", "info", "debug"]

# Type alias for a command context or an interaction.
ContextOrInteraction = commands.Context[commands.Bot] | Interaction

# Set initial user to None
sentry_sdk.set_user(None)

from .metrics import (
    record_api_metric,
    record_cache_metric,
    record_cog_metric,
    record_command_metric,
    record_database_metric,
    record_task_metric,
)
from .utils import (
    capture_api_error,
    capture_cog_error,
    capture_database_error,
    capture_exception_safe,
    capture_tux_exception,
    convert_httpx_error,
)

__all__ = [
    # Core classes
    "SentryManager",
    # Dummy implementations for testing
    "DummySpan",
    "DummyTransaction",
    # Context and tagging functions
    "add_breadcrumb",
    "set_command_context",
    "set_context",
    "set_setup_phase_tag",
    "set_span_attributes",
    "set_tag",
    "set_user_context",
    # Span and transaction management
    "enhanced_span",
    "finish_transaction_on_error",
    "get_current_span",
    "span",
    "start_span",
    "start_transaction",
    "transaction",
    # Error capture functions
    "capture_api_error",
    "capture_cog_error",
    "capture_database_error",
    "capture_exception_safe",
    "capture_span_exception",
    "capture_tux_exception",
    "convert_httpx_error",
    # Instrumentation and tracking
    "instrument_bot_commands",
    "safe_set_name",
    "track_command_end",
    "track_command_start",
    # Metrics functions
    "record_api_metric",
    "record_cache_metric",
    "record_cog_metric",
    "record_command_metric",
    "record_database_metric",
    "record_task_metric",
]


class SentryManager:
    """
    Handles all interactions with the Sentry SDK for the bot.

    This class acts as a singleton-like manager (though not strictly enforced)
    for initializing Sentry, capturing events, and managing performance
    monitoring transactions.
    """

    def __init__(self) -> None:
        """Initialize the SentryManager."""
        logger.debug("SentryManager initialized")

    @staticmethod
    def setup() -> None:
        """Initialize Sentry SDK with configuration."""
        setup()

    @staticmethod
    def flush() -> None:
        """Flush pending Sentry events."""
        flush()

    @staticmethod
    def report_signal(signum: int, frame: Any = None) -> None:
        """Report signal reception to Sentry."""
        report_signal(signum, frame)

    @staticmethod
    async def flush_async(flush_timeout: float = 10.0) -> None:
        """Flush pending Sentry events asynchronously."""
        await flush_async(flush_timeout)

    @property
    def is_initialized(self) -> bool:
        """Check if Sentry is initialized."""
        return is_initialized()

    def capture_exception(
        self,
        error: Exception | None = None,
        *,
        contexts: dict[str, dict[str, Any]] | None = None,
        tags: dict[str, Any] | None = None,
        user: discord.User | discord.Member | None = None,
        command_context: ContextOrInteraction | None = None,
        extra: dict[str, Any] | None = None,
        level: LogLevelStr = "error",
        fingerprint: list[str] | None = None,
    ) -> None:
        """
        Capture an exception and send it to Sentry.

        Parameters
        ----------
        error : Exception | None, optional
            The exception to capture. If None, captures the current exception.
        contexts : dict[str, dict[str, Any]] | None, optional
            Additional context data to include.
        tags : dict[str, Any] | None, optional
            Tags to add to the event.
        user : discord.User | discord.Member | None, optional
            User context to include.
        command_context : ContextOrInteraction | None, optional
            Command or interaction context.
        extra : dict[str, Any] | None, optional
            Extra data to include.
        level : LogLevelStr, optional
            The severity level of the event.
        fingerprint : list[str] | None, optional
            Custom fingerprint for grouping events.
        """
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            if contexts:
                for key, value in contexts.items():
                    scope.set_context(key, value)

            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)

            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)

            if fingerprint:
                scope.fingerprint = fingerprint

            if user:
                set_user_context(user)

            if command_context:
                set_command_context(command_context)

            scope.level = level
            sentry_sdk.capture_exception(error)

    def capture_message(self, message: str, level: LogLevelStr = "info") -> None:
        """
        Capture a message and send it to Sentry.

        Parameters
        ----------
        message : str
            The message to capture.
        level : LogLevelStr, optional
            The severity level of the message.
        """
        if not self.is_initialized:
            return

        sentry_sdk.capture_message(message, level=level)

    def set_tag(self, key: str, value: Any) -> None:
        """
        Set a tag in the current Sentry scope.

        Parameters
        ----------
        key : str
            The tag key.
        value : Any
            The tag value.
        """
        set_tag(key, value)

    def set_context(self, key: str, value: dict[str, Any]) -> None:
        """
        Set context data in the current Sentry scope.

        Parameters
        ----------
        key : str
            The context key.
        value : dict[str, Any]
            The context data.
        """
        set_context(key, value)

    def finish_transaction_on_error(self) -> None:
        """Finish the current transaction with error status."""
        finish_transaction_on_error()

    def set_user_context(self, user: discord.User | discord.Member) -> None:
        """
        Set user context for Sentry events.

        Parameters
        ----------
        user : discord.User | discord.Member
            The Discord user to set as context.
        """
        set_user_context(user)

    def set_command_context(self, ctx: ContextOrInteraction) -> None:
        """
        Set command context for Sentry events.

        Parameters
        ----------
        ctx : ContextOrInteraction
            The command context or interaction.
        """
        set_command_context(ctx)

    def get_current_span(self) -> Any | None:
        """
        Get the current active Sentry span.

        Returns
        -------
        Any | None
            The current span, or None if no span is active.
        """
        return get_current_span()

    def start_transaction(self, op: str, name: str) -> Any:
        """
        Start a new Sentry transaction.

        Parameters
        ----------
        op : str
            The operation type.
        name : str
            The transaction name.

        Returns
        -------
        Any
            The started transaction object.
        """
        return start_transaction(op, name)

    def start_span(self, op: str, name: str = "") -> Any:
        """
        Start a new Sentry span.

        Parameters
        ----------
        op : str
            The operation name for the span.
        name : str, optional
            The name of the span.

        Returns
        -------
        Any
            The started span object.
        """
        return start_span(op, name)

    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: LogLevelStr = "info",
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a breadcrumb to the current Sentry scope.

        Parameters
        ----------
        message : str
            The breadcrumb message.
        category : str, optional
            The breadcrumb category.
        level : LogLevelStr, optional
            The breadcrumb level.
        data : dict[str, Any] | None, optional
            Additional data for the breadcrumb.
        """
        add_breadcrumb(message, category, level, data)

    def track_command_start(self, command_name: str) -> None:
        """
        Track command execution start time.

        Parameters
        ----------
        command_name : str
            The name of the command being executed.
        """
        track_command_start(command_name)

    def track_command_end(
        self,
        command_name: str,
        success: bool,
        error: Exception | None = None,
    ) -> None:
        """
        Track command execution end and performance metrics.

        Parameters
        ----------
        command_name : str
            The name of the command that finished.
        success : bool
            Whether the command executed successfully.
        error : Exception | None, optional
            The error that occurred, if any.
        """
        track_command_end(command_name, success, error)
