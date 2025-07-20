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

from types import FrameType
from typing import Any, ClassVar, Literal, cast

import discord
import sentry_sdk
from discord import Interaction
from discord.ext import commands
from loguru import logger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration
from sentry_sdk.types import Event, Hint

from tux.utils.config import CONFIG
from tux.utils.context_utils import get_interaction_context
from tux.utils.env import get_current_env

# Type alias for Sentry's log level strings.
LogLevelStr = Literal["fatal", "critical", "error", "warning", "info", "debug"]

# Type alias for a command context or an interaction.
ContextOrInteraction = commands.Context[commands.Bot] | Interaction

sentry_sdk.set_user(None)


class SentryManager:
    """
    Handles all interactions with the Sentry SDK for the bot.

    This class acts as a singleton-like manager (though not strictly enforced)
    for initializing Sentry, capturing events, and managing performance
    monitoring transactions.
    """

    # Standard Sentry transaction statuses.
    # See: https://develop.sentry.dev/sdk/event-payloads/transaction/#transaction-status
    STATUS: ClassVar[dict[str, str]] = {
        "OK": "ok",
        "UNKNOWN": "unknown",
        "ERROR": "internal_error",
        "NOT_FOUND": "not_found",
        "PERMISSION_DENIED": "permission_denied",
        "INVALID_ARGUMENT": "invalid_argument",
        "RESOURCE_EXHAUSTED": "resource_exhausted",
        "UNAUTHENTICATED": "unauthenticated",
        "CANCELLED": "cancelled",
    }

    def __init__(self) -> None:
        """Initialize the SentryManager."""
        self.active_sentry_transactions: dict[int, Any] = {}

    # --- Setup & Lifecycle ---

    @staticmethod
    def _before_send(event: Event, hint: Hint) -> Event | None:
        """
        Filter and sanitize events before sending to Sentry.

        This hook allows us to:
        - Remove sensitive information
        - Filter out noisy errors
        - Add error fingerprinting for better grouping
        - Drop events we don't want to track
        """
        # Filter out known noisy errors that provide little value
        if "exc_info" in hint:
            exc_type, exc_value, _ = hint["exc_info"]

            # Filter out network-related errors that are usually not actionable
            if exc_type.__name__ in ("ConnectionResetError", "ConnectionAbortedError", "TimeoutError"):
                return None

            # Add custom fingerprinting for Discord errors
            if exc_type.__name__.startswith("Discord"):
                event["fingerprint"] = [exc_type.__name__, str(getattr(exc_value, "code", "unknown"))]

            # Add fingerprinting for database errors
            elif exc_type.__name__ in ("DatabaseError", "OperationalError", "IntegrityError"):
                # Group database errors by type and first few words of message
                error_msg = str(exc_value)[:50] if exc_value else "unknown"
                event["fingerprint"] = ["database_error", exc_type.__name__, error_msg]

            # Add fingerprinting for command errors
            elif exc_type.__name__.endswith("CommandError"):
                command_name = event.get("tags", {}).get("command", "unknown")
                event["fingerprint"] = ["command_error", exc_type.__name__, command_name]

        # Basic data sanitization - remove potentially sensitive info
        # Remove sensitive data from request context if present
        if "request" in event:
            request = event["request"]
            if "query_string" in request:
                request["query_string"] = "[REDACTED]"
            if "cookies" in request:
                request["cookies"] = "[REDACTED]"

        return event

    @staticmethod
    def _get_span_operation_mapping(op: str) -> str:
        """
        Map database controller operations to standardized operation types.

        Parameters
        ----------
        op : str
            The original operation name

        Returns
        -------
        str
            The standardized operation type
        """
        if not op.startswith("db.controller."):
            return op

        # Use dictionary lookup instead of if/elif chain
        operation_mapping = {
            "get_": "db.read",
            "find_": "db.read",
            "create_": "db.create",
            "update_": "db.update",
            "increment_": "db.update",
            "delete_": "db.delete",
            "count_": "db.count",
        }

        return next((mapped_op for prefix, mapped_op in operation_mapping.items() if prefix in op), "db.other")

    @staticmethod
    def _get_transaction_operation_mapping(transaction_name: str) -> str:
        """
        Map database controller transaction names to standardized operation types.

        Parameters
        ----------
        transaction_name : str
            The original transaction name

        Returns
        -------
        str
            The standardized transaction operation type
        """
        if not transaction_name.startswith("db.controller."):
            return transaction_name

        # Use dictionary lookup instead of if/elif chain
        operation_mapping = {
            "get_": "db.controller.read_operation",
            "find_": "db.controller.read_operation",
            "create_": "db.controller.create_operation",
            "update_": "db.controller.update_operation",
            "increment_": "db.controller.update_operation",
            "delete_": "db.controller.delete_operation",
            "count_": "db.controller.count_operation",
        }

        return next(
            (mapped_op for prefix, mapped_op in operation_mapping.items() if prefix in transaction_name),
            "db.controller.other_operation",
        )

    @staticmethod
    def _filter_and_group_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter and group spans to reduce noise and improve trace readability.

        Parameters
        ----------
        spans : list[dict[str, Any]]
            List of spans to filter and group

        Returns
        -------
        list[dict[str, Any]]
            Filtered and grouped spans
        """
        filtered_spans: list[dict[str, Any]] = []

        for span in spans:
            op = span.get("op", "")
            description = span.get("description", "")

            # Filter out internal Prisma HTTP requests to the query engine
            if op == "http.client" and "localhost" in description:
                continue

            # Filter out noisy, low-level asyncio/library functions
            if "staggered_race" in description:
                continue

            # Group database controller operations for cleaner reporting
            if "db.controller." in op:
                span["op"] = SentryManager._get_span_operation_mapping(op)
                # Normalize description for grouped DB operations
                span["description"] = f"DB {str(span['op']).split('.')[-1].capitalize()} Operation"

            filtered_spans.append(span)

        return filtered_spans

    @staticmethod
    def _before_send_transaction(event: Event, hint: Hint) -> Event | None:
        """
        Filter and modify transaction events before sending to Sentry.

        This helps reduce noise and improve transaction grouping.
        """
        if event.get("type") != "transaction":
            return event

        transaction_name = event.get("transaction", "")

        # Filter out noisy or uninteresting transactions entirely
        noisy_operations = [
            "safe_get_attr",
            "connect_or_create",
            "_build_",
            "_add_include",
            "CogLoader.load_cogs_from_folder",  # Startup noise
            "CogLoader Setup",  # More startup noise
            "Bot shutdown process",  # Shutdown noise
        ]

        if any(op in transaction_name for op in noisy_operations):
            return None

        # Filter spans to reduce noise and group operations
        if "spans" in event:
            spans = cast(list[dict[str, Any]], event.get("spans") or [])
            event["spans"] = SentryManager._filter_and_group_spans(spans)

        # Group all database controller transactions by type for cleaner reporting
        if "db.controller." in transaction_name:
            event["transaction"] = SentryManager._get_transaction_operation_mapping(transaction_name)

        return event

    @staticmethod
    def _traces_sampler(sampling_context: dict[str, Any]) -> float:
        """
        Custom trace sampling function for more granular control over which traces to sample.

        Parameters
        ----------
        sampling_context : dict[str, Any]
            Context information about the transaction

        Returns
        -------
        float
            Sampling rate between 0.0 and 1.0
        """
        # Get transaction name for decision making
        transaction_name = sampling_context.get("transaction_context", {}).get("name", "")

        # Full sampling in development for debugging
        if get_current_env() in ("dev", "development"):
            return 1.0

        # Production sampling rates using dictionary lookup
        sampling_rates = {
            "db.controller": 0.01,  # 1% sampling for DB operations
            "db.query": 0.005,  # 0.5% sampling for low-level DB queries
            "command": 0.1,  # 10% sampling for commands
            "cog.": 0.02,  # 2% sampling for cog ops
        }

        # Check for matching patterns and return appropriate sampling rate
        return next(
            (rate for pattern, rate in sampling_rates.items() if pattern in transaction_name),
            0.05,  # Default sampling rate for other operations
        )

    @staticmethod
    def setup() -> None:
        """
        Initializes the Sentry SDK with configuration from the environment.

        If no Sentry DSN is provided in the configuration, setup is skipped.
        This method configures the release version, environment, tracing, and
        enables Sentry's logging integration.
        """
        if not CONFIG.SENTRY_DSN:
            logger.warning("No Sentry DSN configured, skipping Sentry setup")
            return

        logger.info("Setting up Sentry...")

        try:
            sentry_sdk.init(
                # https://docs.sentry.io/platforms/python/configuration/options/#dsn
                dsn=CONFIG.SENTRY_DSN,
                # https://docs.sentry.io/platforms/python/configuration/options/#release
                release=CONFIG.BOT_VERSION,
                # https://docs.sentry.io/platforms/python/configuration/options/#environment
                environment=get_current_env(),
                integrations=[
                    AsyncioIntegration(),
                    LoguruIntegration(),
                ],
                enable_tracing=True,
                # https://docs.sentry.io/platforms/python/configuration/options/#attach_stacktrace
                attach_stacktrace=True,
                # https://docs.sentry.io/platforms/python/configuration/options/#send_default_pii
                send_default_pii=False,
                # https://docs.sentry.io/platforms/python/configuration/options/#traces_sample_rate
                # Adjust sampling based on environment - 100% for dev, lower for production
                traces_sample_rate=1.0 if get_current_env() in ("dev", "development") else 0.1,
                # Set profiles_sample_rate to profile transactions.
                # We recommend adjusting this value in production.
                profiles_sample_rate=1.0 if get_current_env() in ("dev", "development") else 0.01,
                # https://docs.sentry.io/platforms/python/configuration/filtering/#using-before-send
                before_send=SentryManager._before_send,
                before_send_transaction=SentryManager._before_send_transaction,
                # Custom trace sampling function for more granular control
                traces_sampler=SentryManager._traces_sampler,
                _experiments={
                    "enable_logs": True,
                },
            )
            sentry_sdk.set_tag("discord_library_version", discord.__version__)
            logger.info(f"Sentry initialized: {sentry_sdk.is_initialized()}")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    @staticmethod
    def _set_signal_scope_tags(scope: Any, signum: int) -> None:
        """Set signal-related tags on a Sentry scope.

        Parameters
        ----------
        scope : Any
            The Sentry scope to modify
        signum : int
            The signal number
        """
        tags = {
            "signal.number": signum,
            "lifecycle.event": "termination_signal",
        }

        for key, value in tags.items():
            scope.set_tag(key, value)

    @staticmethod
    def report_signal(signum: int, _frame: FrameType | None) -> None:
        """
        A signal handler that reports termination signals to Sentry.

        This method is designed to be used with Python's `signal` module.
        It captures signals like SIGTERM and SIGINT, adds context to Sentry,
        and then raises a `KeyboardInterrupt` to trigger the bot's graceful
        shutdown sequence.

        Parameters
        ----------
        signum : int
            The signal number received.
        _frame : FrameType | None
            The current stack frame at the time of the signal.
        """
        if sentry_sdk.is_initialized():
            with sentry_sdk.push_scope() as scope:
                SentryManager._set_signal_scope_tags(scope, signum)
                sentry_sdk.add_breadcrumb(
                    category="lifecycle",
                    message=f"Received termination signal {signum}",
                    level="info",
                )
        raise KeyboardInterrupt

    @staticmethod
    def flush() -> None:
        """
        Flushes all pending Sentry events.

        This should be called during the application's shutdown sequence to
        ensure that all buffered events are sent before the process exits.
        """
        if sentry_sdk.is_initialized():
            sentry_sdk.flush()

    @property
    def is_initialized(self) -> bool:
        """
        A convenience property to check if the Sentry SDK is active.

        Returns
        -------
        bool
            True if Sentry is initialized, False otherwise.
        """
        return sentry_sdk.is_initialized()

    # --- Event Capturing & Context ---

    def capture_exception(
        self,
        error: Exception,
        *,
        context: dict[str, Any] | None = None,
        level: LogLevelStr = "error",
        tags: dict[str, str] | None = None,
    ) -> str | None:
        """
        Captures and reports an exception to Sentry.

        This method enriches the exception report with additional context
        and tags, providing more insight into the error.

        Parameters
        ----------
        error : Exception
            The exception object to capture.
        context : dict[str, Any] | None, optional
            A dictionary of context data to attach to the event.
        level : LogLevelStr, optional
            The severity level for the event (e.g., 'error', 'warning').
        tags : dict[str, str] | None, optional
            Additional key-value tags to associate with the event.

        Returns
        -------
        str | None
            The Sentry event ID if capture was successful, otherwise None.
        """
        if not self.is_initialized:
            return None

        event_id: str | None = None
        try:
            with sentry_sdk.push_scope() as scope:
                if context:
                    self._set_scope_context(scope, context)

                scope.level = level

                if tags:
                    for key, value in tags.items():
                        scope.set_tag(key, value)

                event_id = sentry_sdk.capture_exception(error)

                if event_id:
                    logger.trace(f"Reported {type(error).__name__} to Sentry ({event_id})")
                else:
                    logger.warning(f"Captured {type(error).__name__} but Sentry returned no ID.")
        except Exception as e:
            logger.error(f"Failed to report {type(error).__name__} to Sentry: {e}")

        return event_id

    def capture_message(self, message: str, level: LogLevelStr = "info") -> None:
        """
        Captures and reports a message to Sentry.

        Parameters
        ----------
        message : str
            The message string to report.
        level : LogLevelStr, optional
            The severity level for the message.
        """
        if self.is_initialized:
            with sentry_sdk.push_scope() as scope:
                scope.set_level(level)
                sentry_sdk.capture_message(message)
                logger.trace(f"Captured message in Sentry: {message}")

    def set_tag(self, key: str, value: Any) -> None:
        """
        Sets a tag in the current Sentry scope.

        Tags are indexed key-value pairs that can be used for searching
        and filtering events in Sentry.

        Parameters
        ----------
        key : str
            The name of the tag.
        value : Any
            The value of the tag.
        """
        if self.is_initialized:
            sentry_sdk.set_tag(key, value)
            logger.trace(f"Set Sentry tag: {key}={value}")

    def set_context(self, key: str, value: dict[str, Any]) -> None:
        """
        Sets context data in the current Sentry scope.

        Context provides additional, non-indexed data that is displayed
        on the Sentry event page.

        Parameters
        ----------
        key : str
            The name of the context group (e.g., 'discord', 'user_info').
        value : dict[str, Any]
            A dictionary of context data.
        """
        if self.is_initialized:
            sentry_sdk.set_context(key, value)
            logger.trace(f"Set Sentry context for {key}.")

    # --- Transaction Management ---

    def finish_transaction_on_error(self) -> None:
        """
        Finds and finishes an active Sentry transaction with an error status.

        This method should be called from an error handler. It automatically
        accesses the current span and sets its status to 'internal_error'.
        """
        if not self.is_initialized:
            return

        if span := sentry_sdk.get_current_span():
            span.set_status(self.STATUS["ERROR"])
            logger.trace("Set Sentry span status to 'internal_error' for errored command.")

    # --- Internal Helpers ---

    def _set_scope_context(self, scope: Any, context: dict[str, Any]) -> None:
        """
        Sets user, context, and tags on a Sentry scope from a context dictionary.

        Parameters
        ----------
        scope : Any
            The Sentry scope object to modify.
        context : dict[str, Any]
            A dictionary of context data.
        """
        scope.set_user({"id": context.get("user_id"), "username": context.get("user_name")})
        scope.set_context("discord", context)

        # Set tags using a dictionary to avoid repetitive set_tag calls
        tags = {
            "command_name": context.get("command_name", "Unknown"),
            "command_type": context.get("command_type", "Unknown"),
            "guild_id": str(context.get("guild_id")) if context.get("guild_id") else "DM",
        }

        for key, value in tags.items():
            scope.set_tag(key, value)

    def set_user_context(self, user: discord.User | discord.Member) -> None:
        """
        Sets the user context for the current Sentry scope.

        This provides valuable information for debugging user-specific issues.

        Parameters
        ----------
        user : discord.User | discord.Member
            The Discord user or member to set as context.
        """
        if not self.is_initialized:
            return

        user_data: dict[str, Any] = {
            "id": str(user.id),
            "username": user.name,
            "display_name": user.display_name,
            "bot": user.bot,
            "created_at": user.created_at.isoformat(),
        }

        # Add member-specific data if available
        if isinstance(user, discord.Member):
            member_data = {
                "guild_id": str(user.guild.id),
                "guild_name": user.guild.name,
                "nick": user.nick,
                "joined_at": user.joined_at.isoformat() if user.joined_at else None,
                "roles": [role.name for role in user.roles[1:]],  # Exclude @everyone
                "premium_since": user.premium_since.isoformat() if user.premium_since else None,
            }
            user_data |= member_data

        sentry_sdk.set_user(user_data)
        logger.trace(f"Set Sentry user context for {user.name}")

    def set_command_context(self, ctx: ContextOrInteraction) -> None:
        """
        Sets comprehensive command context for the current Sentry scope using existing context utilities.

        This enriches error reports with command-specific information.

        Parameters
        ----------
        ctx : ContextOrInteraction
            The command context or interaction.
        """
        if not self.is_initialized:
            return

        # Use existing context utilities to get standardized context data
        context_data = get_interaction_context(ctx)

        # Set user context
        user = ctx.user if isinstance(ctx, Interaction) else ctx.author
        self.set_user_context(user)

        # Set guild context if available
        if ctx.guild:
            guild_data = {
                "id": str(ctx.guild.id),
                "name": ctx.guild.name,
                "member_count": ctx.guild.member_count,
                "created_at": ctx.guild.created_at.isoformat(),
                "owner_id": str(ctx.guild.owner_id) if ctx.guild.owner_id else None,
                "verification_level": ctx.guild.verification_level.name,
                "premium_tier": ctx.guild.premium_tier,
                "preferred_locale": str(ctx.guild.preferred_locale),
            }
            self.set_context("guild", guild_data)

        # Set command context using standardized data
        self.set_context("command", context_data)

    # --- Tracing and Span Management ---

    def get_current_span(self) -> Any | None:
        """
        Get the current active span from Sentry.

        Returns
        -------
        Any | None
            The current span if Sentry is initialized and a span is active, None otherwise.
        """
        return sentry_sdk.get_current_span() if self.is_initialized else None

    def start_transaction(self, op: str, name: str, description: str = "") -> Any:
        """
        Start a new Sentry transaction.

        Parameters
        ----------
        op : str
            The operation name for the transaction.
        name : str
            The name of the transaction.
        description : str, optional
            A description of the transaction.

        Returns
        -------
        Any
            The started transaction object.
        """
        return (
            sentry_sdk.start_transaction(
                op=op,
                name=name,
                description=description,
            )
            if self.is_initialized
            else None
        )

    def start_span(self, op: str, description: str = "") -> Any:
        """
        Start a new Sentry span.

        Parameters
        ----------
        op : str
            The operation name for the span.
        description : str, optional
            A description of the span.

        Returns
        -------
        Any
            The started span object.
        """
        return sentry_sdk.start_span(op=op, description=description) if self.is_initialized else None

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
        if not self.is_initialized:
            return
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data,
        )
