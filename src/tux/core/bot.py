"""
Tux Discord bot core implementation.

This module defines the main Tux bot class, which extends discord.py's Bot
and provides comprehensive lifecycle management including setup orchestration,
cog loading, database integration, error handling, telemetry, and graceful
resource cleanup.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import discord
from discord.ext import commands
from loguru import logger
from rich.console import Console

from tux.core.setup.orchestrator import BotSetupOrchestrator
from tux.core.task_monitor import TaskMonitor
from tux.database.controllers import DatabaseCoordinator
from tux.database.service import DatabaseService
from tux.services.emoji_manager import EmojiManager
from tux.services.http_client import http_client
from tux.services.sentry import (
    SentryManager,
    capture_database_error,
    capture_exception_safe,
)
from tux.services.sentry.tracing import (
    instrument_bot_commands,
    start_span,
    start_transaction,
)
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxDatabaseConnectionError
from tux.shared.version import get_version
from tux.ui.banner import create_banner

__all__ = ["Tux"]


class Tux(commands.Bot):
    """
    Main bot class for Tux, extending discord.py's commands.Bot.

    This class orchestrates the complete bot lifecycle including database
    connections, cog loading, Sentry telemetry, background task monitoring,
    and graceful shutdown procedures.

    Attributes
    ----------
    is_shutting_down : bool
        Flag indicating if shutdown is in progress (prevents duplicate shutdown).
    setup_complete : bool
        Flag indicating if initial setup has completed successfully.
    start_time : float | None
        Unix timestamp when bot became ready, used for uptime calculations.
    setup_task : asyncio.Task[None] | None
        Background task that handles async initialization.
    task_monitor : TaskMonitor
        Manages background tasks and ensures proper cleanup.
    db_service : DatabaseService
        Database connection manager and query executor.
    sentry_manager : SentryManager
        Error tracking and telemetry manager.
    prefix_manager : Any | None
        Cache manager for guild-specific command prefixes.
    emoji_manager : EmojiManager
        Custom emoji resolver for the bot.
    console : Console
        Rich console for formatted terminal output.
    uptime : float
        Unix timestamp when bot instance was created.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the Tux bot and schedule async setup.

        The actual bot setup happens asynchronously in the setup task to avoid
        blocking initialization. The setup task is created after a brief delay
        to ensure the event loop is ready.

        Parameters
        ----------
        *args : Any
            Positional arguments passed to discord.py's Bot.__init__.
        **kwargs : Any
            Keyword arguments passed to discord.py's Bot.__init__.
        """
        super().__init__(*args, **kwargs)

        # Core state flags for lifecycle tracking
        self.is_shutting_down: bool = False
        self.setup_complete: bool = False
        self.start_time: float | None = None
        self.setup_task: asyncio.Task[None] | None = None

        # Internal flags to prevent duplicate initialization
        self._emoji_manager_initialized: bool = False
        self._banner_logged: bool = False
        self._startup_task: asyncio.Task[None] | None = None
        self._commands_instrumented: bool = False

        # Background task monitor (manages periodic tasks and cleanup)
        self.task_monitor = TaskMonitor(self)

        # Service integrations
        self.db_service = DatabaseService()
        self._db_coordinator: DatabaseCoordinator | None = None  # Cached coordinator
        self.sentry_manager = SentryManager()
        self.prefix_manager: Any | None = None  # Initialized during setup

        # UI components
        self.emoji_manager = EmojiManager(self)
        self.console = Console(stderr=True, force_terminal=True)
        self.uptime = discord.utils.utcnow().timestamp()

        logger.debug("Bot initialization complete")

        # Schedule setup task creation on the next event loop iteration
        # This ensures the event loop is fully ready before we create async tasks
        asyncio.get_event_loop().call_soon(self.create_setup_task)

    def create_setup_task(self) -> None:
        """
        Create the async setup task in the proper event loop context.

        Called by ``call_soon`` to ensure we're in the event loop's execution
        context. Prevents ``RuntimeError`` when creating tasks too early.
        """
        if self.setup_task is None:
            logger.debug("Creating bot setup task")
            self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")

    async def setup(self) -> None:
        """
        Perform one-time bot setup and initialization.

        Delegates to BotSetupOrchestrator which handles database connection,
        cog loading, cache initialization, and background task startup. Uses
        lazy import of BotSetupOrchestrator to avoid circular dependencies.
        All setup operations are traced with Sentry spans for monitoring.

        Raises
        ------
        RuntimeError
            If database setup fails (wrapped from connection errors).
        """
        try:
            with start_span("bot.setup", "Bot setup process") as span:
                orchestrator = BotSetupOrchestrator(self)
                await orchestrator.setup(span)

        except TuxDatabaseConnectionError as e:
            # Database connection or migration failure is critical - provide helpful error message
            # Error details already logged by database service, just provide hint
            logger.info("To start the database, run: docker compose up")
            logger.info("To run migrations manually, run: uv run db push")
            capture_database_error(e, operation="connection")
            # Re-raise the original exception to preserve error type
            raise
        except ConnectionError as e:
            # Wrap generic connection errors in TuxDatabaseConnectionError
            # Error details already logged by database service, just provide hint
            logger.info("To start the database, run: docker compose up")
            capture_database_error(e, operation="connection")
            msg = "Database setup failed"
            raise TuxDatabaseConnectionError(msg) from e

    @property
    def db(self) -> DatabaseCoordinator:
        """
        Get the database coordinator for accessing database controllers.

        Provides convenient access to database operations via controllers like
        ``bot.db.guild_config.get_guild_config()``. The coordinator is cached
        to avoid creating new instances on every access.

        Returns
        -------
        DatabaseCoordinator
            Coordinator providing access to all database controllers.
        """
        if self._db_coordinator is None:
            self._db_coordinator = DatabaseCoordinator(self.db_service)
        return self._db_coordinator

    async def setup_hook(self) -> None:
        """
        Discord.py lifecycle hook called before connecting to Discord.

        Initializes the emoji manager, checks setup task status, and schedules
        post-ready startup tasks. This is a discord.py callback that runs after
        __init__ but before the bot connects to Discord.
        """
        # Initialize emoji manager (loads custom emojis, etc.)
        if not self._emoji_manager_initialized:
            await self.emoji_manager.init()
            self._emoji_manager_initialized = True

        # Check if setup task has completed
        if self.setup_task and self.setup_task.done():
            # Check if setup raised an exception
            if getattr(self.setup_task, "_exception", None) is not None:
                self.setup_complete = False
                # Don't schedule post-ready startup if setup failed
                return

            # Setup completed successfully
            self.setup_complete = True
            logger.info("Bot setup completed successfully")

            # Tag success in Sentry for monitoring
            if self.sentry_manager.is_initialized:
                self.sentry_manager.set_tag("bot.setup_complete", True)

        # Schedule post-ready startup (banner, stats, instrumentation)
        # Only schedule if setup succeeded or is still running
        if (
            self.setup_complete or (self.setup_task and not self.setup_task.done())
        ) and (self._startup_task is None or self._startup_task.done()):
            self._startup_task = self.loop.create_task(self._post_ready_startup())

    async def _post_ready_startup(self) -> None:
        """
        Execute post-ready startup tasks after bot is fully connected.

        Waits for both Discord READY and internal setup completion, then performs
        final initialization: records start time, displays startup banner,
        instruments commands for Sentry tracing, and records initial bot statistics.
        """
        # Wait for Discord connection and READY event
        await self.wait_until_ready()

        # Wait for internal bot setup (cogs, database, caches) to complete
        await self._wait_for_setup()

        # Record the timestamp when bot became fully operational
        if not self.start_time:
            self.start_time = discord.utils.utcnow().timestamp()

        # Display startup banner with bot info (once only)
        if not self._banner_logged:
            await self._log_startup_banner()
            self._banner_logged = True

        # Enable Sentry command tracing (once only, after cogs loaded)
        if not self._commands_instrumented and self.sentry_manager.is_initialized:
            try:
                instrument_bot_commands(self)
                self._commands_instrumented = True
                logger.info("Sentry command instrumentation enabled")
            except Exception as e:
                logger.error(f"Failed to instrument commands for Sentry: {e}")
                capture_exception_safe(e)

        # Record initial bot statistics to Sentry context
        self._record_bot_stats()

    def get_prefix_cache_stats(self) -> dict[str, int]:
        """
        Get prefix cache statistics for monitoring.

        Returns zero values if prefix manager is not initialized yet. Used for
        monitoring cache hit rates and performance.

        Returns
        -------
        dict[str, int]
            Dictionary containing prefix cache metrics (cached_prefixes,
            cache_loaded, default_prefix).
        """
        if self.prefix_manager:
            return self.prefix_manager.get_cache_stats()
        return {"cached_prefixes": 0, "cache_loaded": 0, "default_prefix": 0}

    def _record_bot_stats(self) -> None:
        """
        Record basic bot statistics to Sentry context for monitoring.

        Captures guild count, user count, channel count, and uptime. This data
        is attached to all Sentry events for debugging context. Only records
        stats if Sentry is initialized. Safe to call repeatedly.
        """
        if not self.sentry_manager.is_initialized:
            return

        self.sentry_manager.set_context(
            "bot_stats",
            {
                "guild_count": len(self.guilds),
                "user_count": len(self.users),
                "channel_count": sum(len(g.channels) for g in self.guilds),
                "uptime": discord.utils.utcnow().timestamp() - (self.start_time or 0),
            },
        )

    async def on_disconnect(self) -> None:
        """
        Discord.py event handler for disconnect events.

        Called when the bot loses connection to Discord. Logs a warning and
        reports to Sentry for monitoring. Disconnects are normal and discord.py
        will automatically attempt to reconnect.
        """
        logger.warning("Bot disconnected from Discord")

        # Report disconnect to Sentry for monitoring patterns
        if self.sentry_manager.is_initialized:
            self.sentry_manager.set_tag("event_type", "disconnect")
            self.sentry_manager.capture_message(
                "Bot disconnected from Discord, this happens sometimes and is fine as long as it's not happening too often",
                level="info",
            )

    async def _wait_for_setup(self) -> None:
        """
        Wait for the setup task to complete if still running.

        If setup fails, triggers bot shutdown to prevent running in a partially
        initialized state. Any exceptions from the setup task are logged and
        captured, then the bot shuts down.
        """
        if self.setup_task and not self.setup_task.done():
            with start_span("bot.wait_setup", "Waiting for setup to complete"):
                try:
                    await self.setup_task

                except Exception as e:
                    # Setup failure is critical - cannot continue in degraded state
                    logger.error(
                        f"Setup failed during on_ready: {type(e).__name__}: {e}",
                    )
                    capture_exception_safe(e)
                    # Trigger shutdown to prevent running with incomplete setup
                    await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shut down the bot and clean up all resources.

        Performs shutdown in three phases: cancel setup task if still running,
        clean up background tasks, and close Discord, database, and HTTP connections.
        This method is idempotent - calling it multiple times is safe. All phases
        are traced with Sentry for monitoring shutdown performance.
        """
        with start_transaction("bot.shutdown", "Bot shutdown process") as transaction:
            # Idempotent guard - prevent duplicate shutdown attempts
            if self.is_shutting_down:
                logger.info("Shutdown already in progress")
                transaction.set_data("already_shutting_down", True)
                return

            self.is_shutting_down = True
            transaction.set_data("shutdown.initiated", True)
            logger.info("Shutting down bot...")

            # Phase 1: Handle setup task if still running
            await self._handle_setup_task()
            transaction.set_data("shutdown.setup_task_handled", True)

            # Phase 2: Clean up background tasks (task monitor)
            await self._cleanup_tasks()
            transaction.set_data("shutdown.tasks_cleaned", True)

            # Phase 3: Close external connections (Discord, DB, HTTP)
            await self._close_connections()
            transaction.set_data("shutdown.connections_closed", True)

            logger.info("Bot shutdown complete")

    async def _handle_setup_task(self) -> None:
        """
        Cancel and wait for the setup task if still running.

        Prevents the setup task from continuing to run during shutdown, which
        could cause errors or resource leaks. Cancellation is graceful - we
        suppress CancelledError and wait for the task to fully terminate.
        """
        with start_span("bot.handle_setup_task", "Handling setup task during shutdown"):
            # Cancel startup task if it exists
            if self._startup_task and not self._startup_task.done():
                self._startup_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._startup_task

            # Cancel setup task if still running
            if self.setup_task and not self.setup_task.done():
                # Cancel the setup task to stop it from continuing
                self.setup_task.cancel()

                # Wait for cancellation to complete, suppressing the expected error
                with contextlib.suppress(asyncio.CancelledError):
                    await self.setup_task

    async def _cleanup_tasks(self) -> None:
        """
        Clean up all background tasks managed by the task monitor.

        Delegates to TaskMonitor which handles canceling and awaiting all
        background tasks (periodic tasks, cleanup tasks, etc.).
        """
        await self.task_monitor.cleanup_tasks()

    async def _close_connections(self) -> None:
        """
        Close all external connections (Discord, database, HTTP client).

        Each connection type is closed independently with error handling to ensure
        one failure doesn't prevent others from closing properly. Closing order:
        Discord gateway/WebSocket connection, database connection pool, then HTTP
        client session. All errors are logged and reported to Sentry but don't
        prevent other resources from being cleaned up.
        """
        with start_span("bot.close_connections", "Closing connections") as span:
            # Close Discord gateway connection
            try:
                logger.debug("Closing Discord connections")
                await self.close()  # discord.py's close method
                logger.debug("Discord connections closed")
                span.set_data("connections.discord_closed", True)

            except Exception as e:
                logger.error(f"Error during Discord shutdown: {e}")
                span.set_data("connections.discord_closed", False)
                span.set_data("connections.discord_error", str(e))
                span.set_data("connections.discord_error_type", type(e).__name__)
                capture_exception_safe(e)

            # Close database connection pool
            try:
                logger.debug("Closing database connections")
                await self.db_service.disconnect()
                logger.debug("Database connections closed")
                span.set_data("connections.db_closed", True)

            except Exception as e:
                logger.error(f"Error during database disconnection: {e}")
                span.set_data("connections.db_closed", False)
                span.set_data("connections.db_error", str(e))
                span.set_data("connections.db_error_type", type(e).__name__)
                capture_exception_safe(e)

            # Close HTTP client session and connection pool
            try:
                logger.debug("Closing HTTP client connections")
                await http_client.close()
                logger.debug("HTTP client connections closed")
                span.set_data("connections.http_closed", True)

            except Exception as e:
                logger.error(f"Error during HTTP client shutdown: {e}")
                span.set_data("connections.http_closed", False)
                span.set_data("connections.http_error", str(e))
                span.set_data("connections.http_error_type", type(e).__name__)
                capture_exception_safe(e)

    async def _log_startup_banner(self) -> None:
        """
        Display the startup banner with bot information.

        Creates and prints a formatted banner showing bot name, version, guild
        count, user count, and configured prefix. Called once after the bot is
        fully ready. The banner is printed to stderr (console) for visibility in logs.
        """
        with start_span("bot.log_banner", "Displaying startup banner"):
            banner = create_banner(
                bot_name=CONFIG.BOT_INFO.BOT_NAME,
                version=get_version(),
                bot_id=str(self.user.id) if self.user else None,
                guild_count=len(self.guilds),
                user_count=len(self.users),
                prefix=CONFIG.get_prefix(),
            )
            self.console.print(banner)
