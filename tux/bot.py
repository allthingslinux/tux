"""Discord bot implementation for Tux.

This module contains the main bot class and implements core functionality
including setup and graceful shutdown.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from typing import Any, ClassVar

import discord
from colorama.ansi import AnsiBack, AnsiFore, AnsiStyle
from discord.ext import commands, tasks
from loguru import logger
from rich.console import Console

from tux.cog_loader import CogLoader
from tux.database.client import db
from tux.utils.banner import create_banner
from tux.utils.config import Config
from tux.utils.emoji import EmojiManager
from tux.utils.env import is_dev_mode

# Create console for rich output
console = Console(stderr=True, force_terminal=True)

# Type hints for colorama
Back: AnsiBack
Fore: AnsiFore
Style: AnsiStyle

# Type hint for discord.ext.tasks.Loop
type TaskLoop = tasks.Loop[Callable[[], Coroutine[Any, Any, None]]]


class DatabaseConnectionError(RuntimeError):
    """Raised when database connection fails."""

    CONNECTION_FAILED = "Failed to establish database connection"


class Tux(commands.Bot):
    """
    Main bot class implementing core functionality.

    The Tux class extends discord.py's Bot class to provide additional functionality
    for managing the bot's lifecycle and resources.

    Attributes
    ----------
    is_shutting_down : bool
        Flag indicating if the bot is in shutdown process
    start_time : float | None
        Timestamp when the bot started, or None if not started
    console : Console
        Rich console for formatted output
    cog_watcher : Any
        Reference to the cog watcher for hot reloading
    """

    _monitor_tasks: ClassVar[TaskLoop]  # type: ignore[name-defined]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the bot and start setup process."""

        super().__init__(*args, **kwargs)

        # Core state
        self.is_shutting_down: bool = False
        self.start_time: float | None = None

        self.cog_watcher: Any = None

        # Managers/utilities
        self.emoji_manager = EmojiManager(self)

        # Create console for rich output
        self.console = Console(stderr=True, force_terminal=True)

    # setup_hook is called by discord.py after login but before connecting to gateway
    async def setup_hook(self) -> None:
        """Perform async setup after login but before connecting to gateway."""
        logger.info("Running setup_hook...")

        try:
            # Order is important: DB -> Emoji Manager -> Extensions -> Monitoring
            await self._setup_database()
            logger.info("Database setup complete in setup_hook.")

            await self.emoji_manager.init()
            logger.info("Emoji manager initialized in setup_hook.")

            await self._load_extensions()
            logger.info("Extensions loaded in setup_hook.")

            self._start_monitoring()  # This starts the @tasks.loop
            logger.info("Task monitoring started in setup_hook.")

            # Do more here as needed

            logger.info("Setup hook completed successfully.")

        except Exception as e:
            logger.critical(f"Critical error during setup_hook: {e}")
            # Consider if bot should proceed or shutdown
            await self.shutdown()
            raise  # Reraise to potentially stop the bot start process

    async def _setup_database(self) -> None:
        """
        Set up database connection.

        Initializes and validates the Prisma client connection.

        Notes
        -----
        Logs connection status and registration state.
        """

        logger.info("Setting up database connection...")

        await db.connect()
        self._validate_db_connection()

        logger.info(f"Database connected: {db.is_connected()}")
        logger.info(f"Database models registered: {db.is_registered()}")

    async def _load_extensions(self) -> None:
        """
        Load bot extensions and cogs.

        Attempts to load:
        1. Jishaku debugging extension
        2. All configured cogs

        Notes
        -----
        Failures to load jishaku are logged but don't prevent other extensions
        from loading.
        """

        try:
            await self.load_extension("jishaku")
            logger.info("Successfully loaded jishaku extension")

        except commands.ExtensionError as e:
            logger.warning(f"Failed to load jishaku: {e}")

        await self.load_cogs()

    def _start_monitoring(self) -> None:
        """
        Start task monitoring loop.

        Initializes the background task that monitors running tasks
        and their states.
        """

        self._monitor_tasks.start()
        logger.debug("Task monitoring started")

    @staticmethod
    def _validate_db_connection() -> None:
        """Validate database connection status.

        Raises
        ------
        DatabaseConnectionError
            If database is not connected or not properly registered
        """

        if not db.is_connected() or not db.is_registered():
            raise DatabaseConnectionError(
                DatabaseConnectionError.CONNECTION_FAILED,
            )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Handle bot ready event.

        Performs initialization tasks when the bot connects to Discord:
        1. Records start time if not set
        2. Ensures setup is complete
        3. Starts hot reloading for cogs (loaded as separate cog)
        4. Logs startup banner

        Notes
        -----
        Will wait for setup to complete if it hasn't finished.
        """

        if not self.start_time:
            self.start_time = discord.utils.utcnow().timestamp()

        # Start hot reloading - import at function level to avoid circular imports
        try:
            await self.load_extension("tux.utils.hot_reload")
            logger.info("Hot reloading enabled")

        except Exception as e:
            logger.warning(f"Failed to enable hot reloading: {e}")

        # Log banner now that setup_hook is done and we're ready!
        await self._log_startup_banner()

    @tasks.loop(seconds=60)
    async def _monitor_tasks(self) -> None:
        """
        Monitor and manage running tasks in the bot. Performs basic task cleanup every 60 seconds.
        """

        try:
            all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            tasks_by_type = self._categorize_tasks(all_tasks)

            await self._cancel_finished_tasks(tasks_by_type)

        except Exception as e:
            logger.error(f"Task monitoring failed: {e}")
            msg = "Critical failure in task monitoring system"

            raise RuntimeError(msg) from e

    def _categorize_tasks(self, tasks: list[asyncio.Task[Any]]) -> dict[str, list[asyncio.Task[Any]]]:
        """Categorize tasks by their type."""

        tasks_by_type: dict[str, list[asyncio.Task[Any]]] = {
            "SCHEDULED": [],  # Tasks from discord.ext.tasks
            "GATEWAY": [],  # Discord gateway/connection tasks
            "SYSTEM": [],  # Asyncio internal tasks
            "COMMAND": [],  # Command invocation tasks
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

    async def _cancel_finished_tasks(self, tasks_by_type: dict[str, list[asyncio.Task[Any]]]) -> None:
        """Cancel and clean up finished tasks."""

        for task_list in tasks_by_type.values():
            for task in task_list:
                if task.done():
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and clean up resources."""

        if self.is_shutting_down:
            logger.info("Shutdown already in progress. Exiting.")
            return

        self.is_shutting_down = True

        logger.info("Shutting down...")

        await self._handle_setup_task()
        await self._cleanup_tasks()
        await self._close_connections()

        logger.info("Shutdown complete.")

    async def _handle_setup_task(self) -> None:
        """Handle setup task during shutdown."""

        # This method is no longer needed as setup_task has been removed.

    async def _cleanup_tasks(self) -> None:
        """Clean up all running tasks."""

        try:
            await self._stop_task_loops()

            all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            tasks_by_type = self._categorize_tasks(all_tasks)

            await self._cancel_tasks(tasks_by_type)

        except Exception as e:
            logger.error(f"Error during task cleanup: {e}")

    async def _stop_task_loops(self) -> None:
        """Stop all task loops in cogs."""

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
                        logger.error(
                            f"Error stopping task loop {cog_name}.{name}: {e}",
                        )

        if hasattr(self, "_monitor_tasks") and self._monitor_tasks.is_running():
            self._monitor_tasks.stop()

    async def _cancel_tasks(self, tasks_by_type: dict[str, list[asyncio.Task[Any]]]) -> None:
        """Cancel tasks by category."""

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

            for task in task_list:
                task.cancel()

            results = await asyncio.gather(*task_list, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error(
                        f"Exception during task cancellation for {task_type}: {result!r}",
                    )

            logger.debug(f"Cancelled {task_type}")

    async def _close_connections(self) -> None:
        """Close Discord and database connections."""

        try:
            logger.debug("Closing Discord connections.")
            await self.close()
            logger.debug("Discord connections closed.")

        except Exception as e:
            logger.error(f"Error during Discord shutdown: {e}")

        try:
            logger.debug("Closing database connections.")
            if db.is_connected():
                await db.disconnect()
                logger.debug("Database connections closed.")
            else:
                logger.warning(
                    "Database was not connected, no disconnect needed.",
                )

        except Exception as e:
            logger.critical(f"Error during database disconnection: {e}")

    async def load_cogs(self) -> None:
        """
        Load cogs using CogLoader.

        Raises
        ------
        Exception
            If cog loading fails

        Notes
        -----
        Uses CogLoader to handle cog discovery and loading.
        """

        logger.info("Loading cogs...")

        try:
            await CogLoader.setup(self)

        except Exception as e:
            logger.critical(f"Error loading cogs: {e}")
            raise

    async def _log_startup_banner(self) -> None:
        """
        Log bot startup information.

        Displays a formatted banner containing:
        - Bot name and version
        - Bot ID
        - Guild and user counts
        - Prefix configuration
        - Development mode status
        """

        # Create and display banner
        banner = create_banner(
            bot_name=str(self.user) if self.user else Config.BOT_NAME,
            version=Config.BOT_VERSION,
            bot_id=str(self.user.id) if self.user else None,
            guild_count=len(self.guilds),
            user_count=len(self.users),
            prefix=Config.DEFAULT_PREFIX,
            dev_mode=is_dev_mode(),
        )

        console.print(banner)
