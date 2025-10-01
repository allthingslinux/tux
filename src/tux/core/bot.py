"""Tux Discord bot core implementation.

Defines the Tux bot class, which extends discord.py's Bot and manages
setup, cog loading, error handling, and resource cleanup.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import discord
from discord.ext import commands
from loguru import logger
from rich.console import Console

from tux.core.task_monitor import TaskMonitor
from tux.database.controllers import DatabaseCoordinator
from tux.database.service import DatabaseService
from tux.services.emoji_manager import EmojiManager
from tux.services.http_client import http_client
from tux.services.sentry import SentryManager, capture_database_error, capture_exception_safe
from tux.services.tracing import (
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
    """Main bot class for Tux, extending discord.py's commands.Bot.

    Responsibilities
    ----------------
    - Connect to the database and validate readiness
    - Load cogs/extensions
    - Configure Sentry tracing and enrich spans
    - Start background task monitoring and perform graceful shutdown
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Tux bot and start setup process."""
        super().__init__(*args, **kwargs)
        # --- Core state ----------------------------------------------------
        self.is_shutting_down: bool = False
        self.setup_complete: bool = False
        self.start_time: float | None = None
        self.setup_task: asyncio.Task[None] | None = None
        self._emoji_manager_initialized = False
        self._hot_reload_loaded = False
        self._banner_logged = False
        self._startup_task: asyncio.Task[None] | None = None
        self._commands_instrumented = False

        # Background task monitor (encapsulates loops/cleanup)
        self.task_monitor = TaskMonitor(self)

        # --- Integration points -------------------------------------------
        # Database service
        self.db_service = DatabaseService()
        # Sentry manager instance for error handling and context utilities
        self.sentry_manager: SentryManager = SentryManager()
        # Prefix manager for efficient prefix resolution
        self.prefix_manager: Any | None = None

        # UI / misc
        self.emoji_manager = EmojiManager(self)
        self.console = Console(stderr=True, force_terminal=True)
        self.uptime = discord.utils.utcnow().timestamp()

        logger.debug("Bot initialization complete")
        # Create setup task after a brief delay to ensure event loop is ready
        asyncio.get_event_loop().call_soon(self._create_setup_task)

    def _create_setup_task(self) -> None:
        """Create the setup task in the proper event loop context."""
        if self.setup_task is None:
            logger.debug("Creating bot setup task")
            self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")

    async def setup(self) -> None:
        """Perform one-time bot setup."""
        try:
            with start_span("bot.setup", "Bot setup process") as span:
                # Lazy import to avoid circular imports
                from tux.core.setup.orchestrator import BotSetupOrchestrator  # noqa: PLC0415

                orchestrator = BotSetupOrchestrator(self)
                await orchestrator.setup(span)
        except (TuxDatabaseConnectionError, ConnectionError) as e:
            logger.error("❌ Database connection failed")
            logger.info("💡 To start the database, run: uv run docker up")
            capture_database_error(e, operation="connection")
            msg = "Database setup failed"
            raise RuntimeError(msg) from e

    @property
    def db(self) -> DatabaseCoordinator:
        """Get the database coordinator for accessing database controllers."""
        return DatabaseCoordinator(self.db_service)

    async def setup_hook(self) -> None:
        """One-time async setup before connecting to Discord (discord.py hook)."""
        if not self._emoji_manager_initialized:
            await self.emoji_manager.init()
            self._emoji_manager_initialized = True

        # Check setup task completion without using callbacks
        if self.setup_task and self.setup_task.done():
            # Handle setup completion here instead of in callback
            if getattr(self.setup_task, "_exception", None) is not None:
                # Setup failed - this will be handled by the main exception handling
                self.setup_complete = False
            else:
                # Setup succeeded
                self.setup_complete = True
                logger.info("✅ Bot setup completed successfully")

                # Record success in Sentry
                if self.sentry_manager.is_initialized:
                    self.sentry_manager.set_tag("bot.setup_complete", True)

        if self._startup_task is None or self._startup_task.done():
            self._startup_task = self.loop.create_task(self._post_ready_startup())

    async def _post_ready_startup(self) -> None:
        """Run after the bot is fully ready.

        Notes
        -----
        - Waits for READY and internal setup
        - Logs the startup banner
        - Instruments commands (Sentry) and records basic bot stats
        """
        await self.wait_until_ready()  # Wait for Discord connection and READY event

        # Also wait for internal bot setup (cogs, db, etc.) to complete
        await self._wait_for_setup()

        if not self.start_time:
            self.start_time = discord.utils.utcnow().timestamp()

        if not self._banner_logged:
            await self._log_startup_banner()
            self._banner_logged = True

        # Instrument commands once, after cogs are loaded and bot is ready
        if not self._commands_instrumented and self.sentry_manager.is_initialized:
            try:
                instrument_bot_commands(self)
                self._commands_instrumented = True
                logger.info("✅ Sentry command instrumentation enabled")
            except Exception as e:
                logger.error(f"⚠️ Failed to instrument commands for Sentry: {e}")
                capture_exception_safe(e)

        self._record_bot_stats()

    def get_prefix_cache_stats(self) -> dict[str, int]:
        """Get prefix cache statistics for monitoring.

        Returns
        -------
        dict[str, int]
            Prefix cache statistics
        """
        if self.prefix_manager:
            return self.prefix_manager.get_cache_stats()
        return {"cached_prefixes": 0, "cache_loaded": 0, "default_prefix": 0}

    def _record_bot_stats(self) -> None:
        """Record basic bot stats to Sentry context (if available)."""
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

    async def on_ready(self) -> None:
        """Handle the Discord READY event."""
        await self._set_presence()

    async def _set_presence(self) -> None:
        """Set the bot's presence (activity and status)."""
        activity = discord.Activity(type=discord.ActivityType.watching, name="for $help")
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_disconnect(self) -> None:
        """Log and report when the bot disconnects from Discord."""
        logger.warning("⚠️ Bot disconnected from Discord")

        if self.sentry_manager.is_initialized:
            self.sentry_manager.set_tag("event_type", "disconnect")
            self.sentry_manager.capture_message(
                "Bot disconnected from Discord, this happens sometimes and is fine as long as it's not happening too often",
                level="info",
            )

    async def _wait_for_setup(self) -> None:
        """Wait for setup to complete, if not already done."""
        if self.setup_task and not self.setup_task.done():
            with start_span("bot.wait_setup", "Waiting for setup to complete"):
                try:
                    await self.setup_task

                except Exception as e:
                    logger.error(f"❌ Setup failed during on_ready: {type(e).__name__}: {e}")
                    capture_exception_safe(e)

                    await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and clean up resources."""
        with start_transaction("bot.shutdown", "Bot shutdown process") as transaction:
            # Idempotent shutdown guard
            if self.is_shutting_down:
                logger.info("Shutdown already in progress")
                transaction.set_data("already_shutting_down", True)
                return

            self.is_shutting_down = True
            transaction.set_tag("shutdown_initiated", True)
            logger.info("🔄 Shutting down bot...")

            await self._handle_setup_task()
            transaction.set_tag("setup_task_handled", True)

            await self._cleanup_tasks()
            transaction.set_tag("tasks_cleaned", True)

            await self._close_connections()
            transaction.set_tag("connections_closed", True)

            logger.info("✅ Bot shutdown complete")

    async def _handle_setup_task(self) -> None:
        """Handle the setup task during shutdown.

        Cancels the setup task when still pending and waits for it to finish.
        """
        with start_span("bot.handle_setup_task", "Handling setup task during shutdown"):
            if self.setup_task and not self.setup_task.done():
                self.setup_task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await self.setup_task

    async def _cleanup_tasks(self) -> None:
        """Clean up all running tasks."""
        await self.task_monitor.cleanup_tasks()

    async def _close_connections(self) -> None:
        """Close Discord and database connections."""
        with start_span("bot.close_connections", "Closing connections") as span:
            try:
                # Discord gateway/session
                logger.debug("Closing Discord connections")

                await self.close()
                logger.debug("Discord connections closed")
                span.set_tag("discord_closed", True)

            except Exception as e:
                logger.error(f"⚠️  Error during Discord shutdown: {e}")

                span.set_tag("discord_closed", False)
                span.set_data("discord_error", str(e))
                capture_exception_safe(e)

            try:
                # Database connection
                logger.debug("Closing database connections")
                await self.db_service.disconnect()
                logger.debug("Database connections closed")
                span.set_tag("db_closed", True)

            except Exception as e:
                logger.error(f"⚠️  Error during database disconnection: {e}")
                span.set_tag("db_closed", False)
                span.set_data("db_error", str(e))

                capture_exception_safe(e)

            try:
                # HTTP client connection pool
                logger.debug("Closing HTTP client connections")
                await http_client.close()
                logger.debug("HTTP client connections closed")
                span.set_tag("http_closed", True)

            except Exception as e:
                logger.error(f"⚠️  Error during HTTP client shutdown: {e}")
                span.set_tag("http_closed", False)
                span.set_data("http_error", str(e))

                capture_exception_safe(e)

    async def _log_startup_banner(self) -> None:
        """Log bot startup information (banner, stats, etc.)."""
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
