"""Tux Discord bot core implementation.

Defines the Tux bot class, which extends discord.py's Bot and manages
setup, cog loading, error handling, and resource cleanup.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from typing import Any

import discord
import sentry_sdk
from discord.ext import commands, tasks
from loguru import logger
from rich.console import Console

from core.cog_loader import CogLoader
from core.config import Config
from core.env import is_dev_mode
from core.utils.banner import create_banner
from core.utils.emoji import EmojiManager
from infra.database.client import db
from infra.sentry import start_span, start_transaction

# Create console for rich output
console = Console(stderr=True, force_terminal=True)

# Type hint for discord.ext.tasks.Loop
type TaskLoop = tasks.Loop[Callable[[], Coroutine[Any, Any, None]]]


class DatabaseConnectionError(RuntimeError):
    """Raised when database connection fails."""

    CONNECTION_FAILED = "Failed to establish database connection"


class Tux(commands.Bot):
    """
    Main bot class for Tux, extending discord.py's Bot.

    Handles setup, cog loading, error handling, Sentry tracing, and resource cleanup.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Tux bot and start setup process."""
        super().__init__(*args, **kwargs)
        # Core state
        self.is_shutting_down: bool = False
        self.setup_complete: bool = False
        self.start_time: float | None = None
        self.setup_task: asyncio.Task[None] | None = None
        self.active_sentry_transactions: dict[int, Any] = {}

        self._emoji_manager_initialized = False
        self._hot_reload_loaded = False
        self._banner_logged = False
        self._startup_task = None

        self.emoji_manager = EmojiManager(self)
        self.console = Console(stderr=True, force_terminal=True)

        logger.debug("Creating bot setup task")
        self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")
        self.setup_task.add_done_callback(self._setup_callback)

    async def setup(self) -> None:
        """Set up the bot: connect to database, load extensions, and start monitoring."""
        try:
            with start_span("bot.setup", "Bot setup process") as span:
                span.set_tag("setup_phase", "starting")
                await self._setup_database()
                span.set_tag("setup_phase", "database_connected")
                await self._load_extensions()
                span.set_tag("setup_phase", "extensions_loaded")
                await self._load_cogs()
                span.set_tag("setup_phase", "cogs_loaded")
                await self._setup_hot_reload()
                span.set_tag("setup_phase", "hot_reload_ready")
                self._start_monitoring()
                span.set_tag("setup_phase", "monitoring_started")

        except Exception as e:
            logger.critical(f"Critical error during setup: {e}")

            if sentry_sdk.is_initialized():
                sentry_sdk.set_context("setup_failure", {"error": str(e), "error_type": type(e).__name__})
                sentry_sdk.capture_exception(e)

            await self.shutdown()
            raise

    async def _setup_database(self) -> None:
        """Set up and validate the database connection."""
        with start_span("bot.database_connect", "Setting up database connection") as span:
            logger.info("Setting up database connection...")

            try:
                await db.connect()
                self._validate_db_connection()

                span.set_tag("db.connected", db.is_connected())
                span.set_tag("db.registered", db.is_registered())

                logger.info(f"Database connected: {db.is_connected()}")
                logger.info(f"Database models registered: {db.is_registered()}")

            except Exception as e:
                span.set_status("internal_error")
                span.set_data("error", str(e))
                raise

    async def _load_extensions(self) -> None:
        """Load bot extensions and cogs, including Jishaku for debugging."""
        with start_span("bot.load_jishaku", "Loading jishaku debug extension") as span:
            try:
                await self.load_extension("jishaku")
                logger.info("Successfully loaded jishaku extension")
                span.set_tag("jishaku.loaded", True)

            except commands.ExtensionError as e:
                logger.warning(f"Failed to load jishaku: {e}")
                span.set_tag("jishaku.loaded", False)
                span.set_data("error", str(e))

    def _start_monitoring(self) -> None:
        """Start the background task monitoring loop."""
        self._monitor_tasks_loop.start()
        logger.debug("Task monitoring started")

    @staticmethod
    def _validate_db_connection() -> None:
        """Raise if the database is not connected or registered."""
        if not db.is_connected() or not db.is_registered():
            raise DatabaseConnectionError(DatabaseConnectionError.CONNECTION_FAILED)

    def _setup_callback(self, task: asyncio.Task[None]) -> None:
        """Handle setup task completion and update setup_complete flag."""
        try:
            task.result()
            self.setup_complete = True
            logger.info("Bot setup completed successfully")

            if sentry_sdk.is_initialized():
                sentry_sdk.set_tag("bot.setup_complete", True)

        except Exception as e:
            logger.critical(f"Setup failed: {e}")
            self.setup_complete = False

            if sentry_sdk.is_initialized():
                sentry_sdk.set_tag("bot.setup_complete", False)
                sentry_sdk.set_tag("bot.setup_failed", True)
                sentry_sdk.capture_exception(e)

    async def setup_hook(self) -> None:
        """discord.py setup_hook: one-time async setup before connecting to Discord."""
        if not self._emoji_manager_initialized:
            await self.emoji_manager.init()
            self._emoji_manager_initialized = True

        if self._startup_task is None or self._startup_task.done():
            self._startup_task = self.loop.create_task(self._post_ready_startup())

    async def _post_ready_startup(self):
        """Run after the bot is fully ready: log banner, set Sentry stats."""
        await self.wait_until_ready()  # Wait for Discord connection and READY event

        # Also wait for internal bot setup (cogs, db, etc.) to complete
        await self._wait_for_setup()

        if not self.start_time:
            self.start_time = discord.utils.utcnow().timestamp()

        if not self._banner_logged:
            await self._log_startup_banner()
            self._banner_logged = True

        if sentry_sdk.is_initialized():
            sentry_sdk.set_context(
                "bot_stats",
                {
                    "guild_count": len(self.guilds),
                    "user_count": len(self.users),
                    "channel_count": sum(len(g.channels) for g in self.guilds),
                    "uptime": discord.utils.utcnow().timestamp() - (self.start_time or 0),
                },
            )

    async def on_ready(self) -> None:
        """Handle bot ready event."""
        await self._wait_for_setup()

        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.watching, name="for /help")
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_disconnect(self) -> None:
        """Log and report when the bot disconnects from Discord."""
        logger.warning("Bot has disconnected from Discord.")

        if sentry_sdk.is_initialized():
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("event_type", "disconnect")
                scope.set_level("info")
                sentry_sdk.capture_message(
                    "Bot disconnected from Discord, this happens sometimes and is fine as long as it's not happening too often",
                )

    # --- Sentry Transaction Tracking ---

    def start_interaction_transaction(self, interaction_id: int, name: str) -> Any:
        """Start a Sentry transaction for a slash command interaction."""
        if not sentry_sdk.is_initialized():
            return None

        transaction = sentry_sdk.start_transaction(
            op="slash_command",
            name=f"Slash Command: {name}",
            description=f"Processing slash command {name}",
        )

        transaction.set_tag("interaction.id", interaction_id)
        transaction.set_tag("command.name", name)
        transaction.set_tag("command.type", "slash")

        self.active_sentry_transactions[interaction_id] = transaction

        return transaction

    def start_command_transaction(self, message_id: int, name: str) -> Any:
        """Start a Sentry transaction for a prefix command."""
        if not sentry_sdk.is_initialized():
            return None

        transaction = sentry_sdk.start_transaction(
            op="prefix_command",
            name=f"Prefix Command: {name}",
            description=f"Processing prefix command {name}",
        )

        transaction.set_tag("message.id", message_id)
        transaction.set_tag("command.name", name)
        transaction.set_tag("command.type", "prefix")

        self.active_sentry_transactions[message_id] = transaction

        return transaction

    def finish_transaction(self, transaction_id: int, status: str = "ok") -> None:
        """Finish a stored Sentry transaction with the given status."""
        if not sentry_sdk.is_initialized():
            return

        if transaction := self.active_sentry_transactions.pop(transaction_id, None):
            transaction.set_status(status)
            transaction.finish()

    async def _wait_for_setup(self) -> None:
        """Wait for setup to complete if not already done."""
        if self.setup_task and not self.setup_task.done():
            with start_span("bot.wait_setup", "Waiting for setup to complete"):
                try:
                    await self.setup_task

                except Exception as e:
                    logger.critical(f"Setup failed during on_ready: {e}")
                    if sentry_sdk.is_initialized():
                        sentry_sdk.capture_exception(e)

                    await self.shutdown()

    @tasks.loop(seconds=60)
    async def _monitor_tasks_loop(self) -> None:
        """Monitor and clean up running tasks every 60 seconds."""
        with start_span("bot.monitor_tasks", "Monitoring async tasks"):
            try:
                all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                tasks_by_type = self._categorize_tasks(all_tasks)
                await self._process_finished_tasks(tasks_by_type)

            except Exception as e:
                logger.error(f"Task monitoring failed: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)

                msg = "Critical failure in task monitoring system"
                raise RuntimeError(msg) from e

    def _categorize_tasks(self, tasks: list[asyncio.Task[Any]]) -> dict[str, list[asyncio.Task[Any]]]:
        """Categorize tasks by their type for monitoring/cleanup."""
        tasks_by_type: dict[str, list[asyncio.Task[Any]]] = {
            "SCHEDULED": [],
            "GATEWAY": [],
            "SYSTEM": [],
            "COMMAND": [],
        }

        for task in tasks:
            if task.done():
                continue

            name = task.get_name()

            if name.startswith("discord-ext-tasks:"):
                tasks_by_type["SCHEDULED"].append(task)
            elif name.startswith(("discord.py:", "discord-voice-", "discord-gateway-")):
                tasks_by_type["GATEWAY"].append(task)
            elif "command_" in name.lower():
                tasks_by_type["COMMAND"].append(task)
            else:
                tasks_by_type["SYSTEM"].append(task)

        return tasks_by_type

    async def _process_finished_tasks(self, tasks_by_type: dict[str, list[asyncio.Task[Any]]]) -> None:
        """Process and clean up finished tasks."""
        for task_list in tasks_by_type.values():
            for task in task_list:
                if task.done():
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and clean up resources."""
        with start_transaction("bot.shutdown", "Bot shutdown process") as transaction:
            if self.is_shutting_down:
                logger.info("Shutdown already in progress. Exiting.")
                transaction.set_data("already_shutting_down", True)
                return

            self.is_shutting_down = True
            transaction.set_tag("shutdown_initiated", True)
            logger.info("Shutting down...")

            await self._handle_setup_task()
            transaction.set_tag("setup_task_handled", True)

            await self._cleanup_tasks()
            transaction.set_tag("tasks_cleaned", True)

            await self._close_connections()
            transaction.set_tag("connections_closed", True)

            logger.info("Bot shutdown complete.")

    async def _handle_setup_task(self) -> None:
        """Handle setup task during shutdown."""
        with start_span("bot.handle_setup_task", "Handling setup task during shutdown"):
            if self.setup_task and not self.setup_task.done():
                self.setup_task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await self.setup_task

    async def _cleanup_tasks(self) -> None:
        """Clean up all running tasks."""
        with start_span("bot.cleanup_tasks", "Cleaning up running tasks"):
            try:
                await self._stop_task_loops()

                all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                tasks_by_type = self._categorize_tasks(all_tasks)

                await self._cancel_tasks(tasks_by_type)

            except Exception as e:
                logger.error(f"Error during task cleanup: {e}")
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)

    async def _stop_task_loops(self) -> None:
        """Stop all task loops in cogs."""
        with start_span("bot.stop_task_loops", "Stopping task loops"):
            for cog_name in self.cogs:
                cog = self.get_cog(cog_name)
                if not cog:
                    continue

                for name, value in cog.__dict__.items():
                    if isinstance(value, tasks.Loop):
                        try:
                            value.stop()
                            logger.debug(f"Stopped task loop {cog_name}.{name}")

                        except Exception as e:
                            logger.error(f"Error stopping task loop {cog_name}.{name}: {e}")

            if hasattr(self, "_monitor_tasks_loop") and self._monitor_tasks_loop.is_running():
                self._monitor_tasks_loop.stop()

    async def _cancel_tasks(self, tasks_by_type: dict[str, list[asyncio.Task[Any]]]) -> None:
        """Cancel tasks by category."""
        with start_span("bot.cancel_tasks", "Cancelling tasks by category") as span:
            for task_type, task_list in tasks_by_type.items():
                if not task_list:
                    continue

                task_names: list[str] = []

                for t in task_list:
                    name = t.get_name() or "unnamed"
                    if name in ("None", "unnamed"):
                        coro = t.get_coro()
                        name = getattr(coro, "__qualname__", str(coro))
                    task_names.append(name)
                names = ", ".join(task_names)

                logger.debug(f"Cancelling {len(task_list)} {task_type}: {names}")
                span.set_data(f"tasks.{task_type.lower()}", task_names)

                for task in task_list:
                    task.cancel()

                results = await asyncio.gather(*task_list, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                        logger.error(f"Exception during task cancellation for {task_type}: {result!r}")

                logger.debug(f"Cancelled {task_type}")

    async def _close_connections(self) -> None:
        """Close Discord and database connections."""
        with start_span("bot.close_connections", "Closing connections") as span:
            try:
                logger.debug("Closing Discord connections.")

                await self.close()
                logger.debug("Discord connections closed.")
                span.set_tag("discord_closed", True)

            except Exception as e:
                logger.error(f"Error during Discord shutdown: {e}")

                span.set_tag("discord_closed", False)
                span.set_data("discord_error", str(e))
                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)

            try:
                logger.debug("Closing database connections.")

                if db.is_connected():
                    await db.disconnect()

                    logger.debug("Database connections closed.")
                    span.set_tag("db_closed", True)

                else:
                    logger.warning("Database was not connected, no disconnect needed.")
                    span.set_tag("db_connected", False)

            except Exception as e:
                logger.critical(f"Error during database disconnection: {e}")
                span.set_tag("db_closed", False)
                span.set_data("db_error", str(e))

                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)

    async def _load_cogs(self) -> None:
        """Load bot cogs using CogLoader."""
        with start_span("bot.load_cogs", "Loading all cogs") as span:
            logger.info("Loading cogs...")

            try:
                await CogLoader.setup(self)
                span.set_tag("cogs_loaded", True)

            except Exception as e:
                logger.critical(f"Error loading cogs: {e}")
                span.set_tag("cogs_loaded", False)
                span.set_data("error", str(e))

                if sentry_sdk.is_initialized():
                    sentry_sdk.capture_exception(e)
                raise

    async def _log_startup_banner(self) -> None:
        """Log bot startup information (banner, stats, etc.)."""
        with start_span("bot.log_banner", "Displaying startup banner"):
            banner = create_banner(
                bot_name=Config.BOT_NAME,
                version=Config.BOT_VERSION,
                bot_id=str(self.user.id) if self.user else None,
                guild_count=len(self.guilds),
                user_count=len(self.users),
                prefix=Config.DEFAULT_PREFIX,
                dev_mode=is_dev_mode(),
            )

            console.print(banner)

    async def _setup_hot_reload(self) -> None:
        """Set up hot reload system after all cogs are loaded."""
        if not self._hot_reload_loaded and "tux.utils.hot_reload" not in self.extensions:
            with start_span("bot.setup_hot_reload", "Setting up hot reload system"):
                try:
                    await self.load_extension("infra.hot_reload")
                    self._hot_reload_loaded = True
                    logger.info("🔥 Hot reload system initialized")
                except Exception as e:
                    logger.error(f"Failed to load hot reload extension: {e}")
                    if sentry_sdk.is_initialized():
                        sentry_sdk.capture_exception(e)
