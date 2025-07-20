"""
Tux Discord bot core implementation.

This module defines the primary `Tux` class, which serves as the central orchestrator
for the entire bot application. It extends `discord.py`'s `commands.Bot` and is
responsible for the following key areas:

- **Lifecycle Management**: Handles the startup and shutdown sequences, ensuring
  that all sub-systems are initialized and terminated gracefully.
- **Component Orchestration**: Initializes and holds instances of various manager
  classes (e.g., `TaskManager`, `SentryManager`, `EmojiManager`) that encapsulate
  specific functionalities.
- **Cog Loading**: Triggers the loading of all command cogs from the `tux/cogs`
  directory via the `CogLoader`.
- **Event Handling**: Implements core `discord.py` event listeners like `on_ready`
  and `setup_hook` to manage the bot's state as it interacts with Discord.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import discord
from discord.ext import commands, tasks
from loguru import logger
from rich.console import Console

from tux.database.client import db
from tux.database.controllers import DatabaseController
from tux.utils.banner import create_banner
from tux.utils.config import CONFIG, Config
from tux.utils.emoji_manager import EmojiManager
from tux.utils.env import is_dev_mode
from tux.utils.sentry_manager import SentryManager
from tux.utils.task_manager import TaskManager
from tux.utils.tracing import instrument_bot_commands, start_span, start_transaction

# Type hint for discord.ext.tasks.Loop
type TaskLoop = tasks.Loop[Callable[[], Coroutine[Any, Any, None]]]


class TaskCategory(Enum):
    """Categories for background tasks."""

    SCHEDULED = auto()
    GATEWAY = auto()
    SYSTEM = auto()
    COMMAND = auto()
    UNKNOWN = auto()


@dataclass
class BotState:
    """Manages the bot's operational state flags."""

    is_shutting_down: bool = False
    setup_complete: bool = False
    start_time: float | None = None
    emoji_manager_initialized: bool = False
    hot_reload_loaded: bool = False
    banner_logged: bool = False


class DatabaseConnectionError(RuntimeError):
    """Raised when database connection fails."""

    CONNECTION_FAILED = "Failed to establish database connection"


class Tux(commands.Bot):
    """
    The main class for the Tux Discord bot.

    This class extends `discord.py`'s `commands.Bot` and serves as the central
    orchestrator for the application. It is responsible for initializing
    sub-systems (like database, Sentry, emoji management), loading cogs,
    handling the bot's lifecycle (setup, shutdown), and processing events.
    """

    # --- Initialization ---

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initializes the Tux bot, its managers, and lifecycle steps.

        This sets up the core state, managers (Sentry, Emoji, Task), and defines
        the sequence of operations for the bot's startup and shutdown routines.
        It also creates and schedules the main setup task.
        """
        super().__init__(*args, **kwargs)

        # Core bot state flags, managed by the BotState dataclass.
        self.state = BotState()
        self.prefix_cache: dict[int, str] = {}
        self.setup_task: asyncio.Task[None] | None = None
        self._startup_task: asyncio.Task[None] | None = None

        # Sub-systems and managers that encapsulate specific functionalities.
        self.sentry_manager = SentryManager()
        self.emoji_manager = EmojiManager(self)
        self.task_manager = TaskManager(self)
        self.console = Console(stderr=True, force_terminal=True)

        # Bot lifecycle routines are defined as lists of (name, function) tuples.
        # This makes the setup and shutdown sequences clear and easy to modify.
        self.setup_steps = [
            ("database", self._setup_database),
            ("jishaku", self._load_jishaku),
            ("cogs", self._load_cogs),
            ("hot_reload", self._setup_hot_reload),
            ("monitoring", self.task_manager.start),
            ("instrument_tasks", self.task_manager.setup_task_instrumentation),
            ("instrument_commands", lambda: instrument_bot_commands(self)),
        ]

        self.shutdown_steps = [
            ("handle_setup_task", self._handle_setup_task),
            ("cleanup_tasks", self.task_manager.cancel_all_tasks),
            ("close_connections", self._close_connections),
        ]

        # The main setup routine is started as a background task immediately.
        logger.debug("Creating bot setup task")
        self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")
        self.setup_task.add_done_callback(self._setup_callback)

    # --- Setup & Lifecycle ---

    async def setup(self) -> None:
        """
        Executes the bot's startup routine in a defined sequence.

        This method iterates through the `setup_steps` list, awaiting each
        asynchronous setup method to ensure the bot is properly initialized
        before it goes online. If any step fails, the setup is aborted, and
        a graceful shutdown is triggered.

        Raises
        ------
        Exception
            Propagates any exception that occurs during a setup step,
            which is then caught, logged, and triggers a shutdown.
        """
        try:
            with start_span("bot.setup", "Bot setup process") as span:
                for name, step_func in self.setup_steps:
                    span.set_tag("setup_phase", f"{name}_starting")
                    if asyncio.iscoroutinefunction(step_func):
                        await step_func()
                    else:
                        step_func()
                    span.set_tag("setup_phase", f"{name}_finished")

        except Exception as e:
            # If any part of the setup fails, log the critical error
            # and initiate a graceful shutdown to prevent a partial startup.
            logger.critical(f"Critical error during setup: {e}")

            self.sentry_manager.set_context("setup_failure", {"error": str(e), "error_type": type(e).__name__})
            self.sentry_manager.capture_exception(e)

            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """
        Executes the bot's shutdown routine in a defined sequence.

        This method ensures that all resources are cleaned up properly,
        including cancelling tasks, stopping task loops, and closing
        database and Discord connections. The `is_shutting_down` flag
        prevents this from running more than once.
        """
        with start_transaction("bot.shutdown", "Bot shutdown process") as transaction:
            # The is_shutting_down flag prevents re-entrant calls to shutdown.
            if self.state.is_shutting_down:
                logger.info("Shutdown already in progress. Exiting.")
                transaction.set_data("already_shutting_down", True)
                return

            self.state.is_shutting_down = True
            transaction.set_tag("shutdown_initiated", True)
            logger.info("Shutting down...")

            # Iterate through the defined shutdown steps.
            for name, step_func in self.shutdown_steps:
                transaction.set_tag(f"{name}_handled", False)
                await step_func()
                transaction.set_tag(f"{name}_handled", True)

            logger.info("Bot shutdown complete.")

    # --- Event Handlers ---

    async def setup_hook(self) -> None:
        """
        Performs one-time async setup before connecting to Discord.

        This `discord.py` hook is used to initialize the emoji manager and
        schedule the `_post_ready_startup` task, which runs after both the
        internal setup and the Discord connection are fully established.
        """
        # Initialize the emoji manager as soon as the bot's loop is running.
        if not self.state.emoji_manager_initialized:
            await self.emoji_manager.init()
            self.state.emoji_manager_initialized = True

        # The `_post_ready_startup` task should only be created once.
        # This check prevents it from being recreated on subsequent reconnects.
        if self._startup_task is None or self._startup_task.done():
            self._startup_task = self.loop.create_task(self._post_ready_startup())

    async def on_ready(self) -> None:
        """
        Called when the bot is ready and connected to Discord.

        This sets the bot's presence and indicates that it is online.
        It waits for the internal setup to complete before proceeding.
        """
        await self._wait_for_setup()

        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.watching, name="for /help")
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_disconnect(self) -> None:
        """
        Logs and reports when the bot disconnects from Discord.

        This is a normal event during bot operation and is usually followed
        by a reconnect, so it is logged as a warning.
        """
        logger.info("Bot has disconnected from Discord.")

        self.sentry_manager.capture_message(
            "Bot disconnected from Discord, this happens sometimes and is fine as long as it's not happening too often",
        )

    # --- Internal Setup & Shutdown Steps ---

    async def _setup_database(self) -> None:
        """
        Connects to the database and validates the connection.

        Raises
        ------
        Exception
            Propagates any database connection errors from the client.
        """
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

    async def _load_jishaku(self) -> None:
        """Loads the Jishaku extension for debugging and development."""
        with start_span("bot.load_jishaku", "Loading jishaku debug extension") as span:
            try:
                await self.load_extension("jishaku")
                logger.info("Successfully loaded jishaku extension")
                span.set_tag("jishaku.loaded", True)

            except commands.ExtensionError as e:
                logger.warning(f"Failed to load jishaku: {e}")
                span.set_tag("jishaku.loaded", False)
                span.set_data("error", str(e))

    async def _load_cogs(self) -> None:
        """
        Loads all command cogs using the CogLoader utility.

        Raises
        ------
        Exception
            Propagates any exceptions that occur during cog loading.
        """
        from tux.cog_loader import CogLoader  # noqa: PLC0415

        with start_span("bot.load_cogs", "Loading all cogs") as span:
            logger.info("Loading cogs...")

            try:
                await CogLoader.setup(self)
                span.set_tag("cogs_loaded", True)

            except Exception as e:
                logger.critical(f"Error loading cogs: {e}")
                span.set_tag("cogs_loaded", False)
                span.set_data("error", str(e))
                self.sentry_manager.capture_exception(e)
                raise

    async def _setup_hot_reload(self) -> None:
        """
        Sets up the hot-reload system for development.

        This allows for automatic reloading of cogs and modules when files
        are changed, speeding up the development workflow.

        Raises
        ------
        Exception
            Propagates exceptions from `load_extension` if hot-reload fails.
        """
        if not self.state.hot_reload_loaded and "tux.utils.hot_reload" not in self.extensions:
            with start_span("bot.setup_hot_reload", "Setting up hot reload system"):
                try:
                    await self.load_extension("tux.utils.hot_reload")
                    self.state.hot_reload_loaded = True
                    logger.info("🔥 Hot reload system initialized")
                except Exception as e:
                    logger.error(f"Failed to load hot reload extension: {e}")
                    self.sentry_manager.capture_exception(e)

    async def _handle_setup_task(self) -> None:
        """
        Handles the main setup task during shutdown.

        If the bot is shut down while the initial setup is still running,
        this method ensures the setup task is properly cancelled.
        """
        with start_span("bot.handle_setup_task", "Handling setup task during shutdown"):
            if self.setup_task and not self.setup_task.done():
                self.setup_task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await self.setup_task

    async def _close_connections(self) -> None:
        """Closes Discord and database connections."""
        with start_span("bot.close_connections", "Closing connections"):
            await self._close_discord()
            await self._close_database()

    async def _close_discord(self) -> None:
        """Closes the connection to the Discord Gateway."""
        with start_span("bot.close_discord", "Closing Discord connection") as span:
            try:
                logger.debug("Closing Discord connection.")
                await self.close()
                logger.debug("Discord connection closed.")
                span.set_tag("discord_closed", True)
            except Exception as e:
                logger.error(f"Error during Discord shutdown: {e}")
                span.set_tag("discord_closed", False)
                span.set_data("discord_error", str(e))
                self.sentry_manager.capture_exception(e)

    async def _close_database(self) -> None:
        """Closes the database connection pool."""
        with start_span("bot.close_database", "Closing database connection") as span:
            if not db.is_connected():
                logger.warning("Database was not connected, no disconnect needed.")
                span.set_tag("db_connected", False)
                return

            try:
                logger.debug("Closing database connection.")
                await db.disconnect()
                logger.debug("Database connection closed.")
                span.set_tag("db_closed", True)
            except Exception as e:
                logger.critical(f"Error during database disconnection: {e}")
                span.set_tag("db_closed", False)
                span.set_data("db_error", str(e))
                self.sentry_manager.capture_exception(e)

    # --- Internal Helpers ---

    def _setup_callback(self, task: asyncio.Task[None]) -> None:
        """
        A callback that runs upon completion of the main setup task.

        This updates the bot's state to reflect whether the setup
        was successful or failed.

        Parameters
        ----------
        task : asyncio.Task[None]
            The setup task that has completed.
        """
        try:
            task.result()
            self.state.setup_complete = True
            logger.info("Bot setup completed successfully")
            self.sentry_manager.set_tag("bot.setup_complete", True)

        except Exception as e:
            logger.critical(f"Setup failed: {e}")
            self.state.setup_complete = False

            self.sentry_manager.set_tag("bot.setup_complete", False)
            self.sentry_manager.set_tag("bot.setup_failed", True)
            self.sentry_manager.capture_exception(e)

    async def _wait_for_setup(self) -> None:
        """
        Waits for the internal setup task to complete before proceeding.

        This is a crucial step in event handlers like `on_ready` to ensure
        that cogs, database connections, etc., are available before the bot
        tries to interact with them.
        """
        if self.setup_task and not self.setup_task.done():
            with start_span("bot.wait_setup", "Waiting for setup to complete"):
                try:
                    await self.setup_task

                except Exception as e:
                    logger.critical(f"Setup failed during on_ready: {e}")
                    self.sentry_manager.capture_exception(e)

                    await self.shutdown()

    async def _post_ready_startup(self):
        """
        Runs tasks that require the bot to be fully online and ready.

        This method waits for two conditions:
        1. The bot is connected to the Discord Gateway (`wait_until_ready`).
        2. The bot has completed its own internal setup (`_wait_for_setup`).

        Once ready, it logs the startup banner and reports initial stats.
        """
        await self.wait_until_ready()

        # Also wait for internal bot setup (cogs, db, etc.) to complete
        await self._wait_for_setup()

        if not self.state.start_time:
            self.state.start_time = discord.utils.utcnow().timestamp()

        if not self.state.banner_logged:
            await self._log_startup_banner()
            self.state.banner_logged = True

        self.sentry_manager.set_context(
            "bot_stats",
            {
                "guild_count": len(self.guilds),
                "user_count": len(self.users),
                "channel_count": sum(len(g.channels) for g in self.guilds),
                "uptime": discord.utils.utcnow().timestamp() - (self.state.start_time or 0),
            },
        )

    async def _log_startup_banner(self) -> None:
        """Logs the bot's startup banner and stats to the console."""
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

            self.console.print(banner)

    @staticmethod
    def _validate_db_connection() -> None:
        """
        Ensures the database is properly connected.

        Raises
        ------
        DatabaseConnectionError
            If the database is not connected or models are not registered.
        """
        if not db.is_connected() or not db.is_registered():
            raise DatabaseConnectionError(DatabaseConnectionError.CONNECTION_FAILED)

    async def _get_prefix(self, bot: Tux, message: discord.Message) -> list[str]:
        """
        Resolves the command prefix for a given message with caching.

        This method dynamically retrieves the command prefix for a guild, caching
        the result to avoid repeated database lookups. It falls back to the
        default prefix if one is not configured or if a database error occurs.
        It also allows the bot to be invoked by mentioning it.

        Parameters
        ----------
        bot : Tux
            The instance of the bot.
        message : discord.Message
            The message to resolve the prefix for.

        Returns
        -------
        list[str]
            A list of command prefixes, including mentions.
        """
        if not message.guild:
            return commands.when_mentioned_or(CONFIG.DEFAULT_PREFIX)(self, message)

        # Check the cache for a stored prefix
        if cached_prefix := self.prefix_cache.get(message.guild.id):
            return commands.when_mentioned_or(cached_prefix)(self, message)

        # If not in cache, query the database
        if db.is_connected():
            try:
                if prefix := await DatabaseController().guild_config.get_guild_prefix(message.guild.id):
                    self.prefix_cache[message.guild.id] = prefix
                    return commands.when_mentioned_or(prefix)(self, message)
            except Exception as e:
                logger.error(f"Error getting guild prefix for guild {message.guild.id}: {e}")
                self.sentry_manager.capture_exception(e)

        # Fallback to the default prefix if no custom one is found
        return commands.when_mentioned_or(CONFIG.DEFAULT_PREFIX)(self, message)

    async def invoke(self, ctx: commands.Context[Any]) -> None:
        """
        Overrides the default invoke method to wrap command execution in a Sentry transaction.

        This ensures that every command invocation is traced, allowing for performance
        monitoring and capturing of related spans (e.g., database queries).

        Parameters
        ----------
        ctx : commands.Context[Any]
            The context of the command invocation.
        """
        if not self.sentry_manager.is_initialized or not ctx.command:
            await super().invoke(ctx)
            return

        # Create a transaction for the command
        op = "command"
        name = ctx.command.qualified_name
        description = ctx.message.content

        with start_transaction(op, name, description):
            # Set comprehensive context using the SentryManager
            self.sentry_manager.set_command_context(ctx)

            # Execute the original command invocation logic
            await super().invoke(ctx)
