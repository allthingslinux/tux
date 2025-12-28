"""
Tux application entrypoint and lifecycle management.

This module provides the orchestration necessary to run Tux,
including command prefix resolution, signal handling, configuration validation,
and structured startup/shutdown flows with Sentry integration.
"""

import asyncio
import contextlib
import signal
from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

from tux.help import TuxHelp
from tux.services.sentry import SentryManager, capture_exception_safe
from tux.shared.config import CONFIG

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = ["TuxApp", "get_prefix"]


async def get_prefix(bot: "Tux", message: discord.Message) -> list[str]:
    """
    Resolve the command prefix for a guild or DM using the prefix manager.

    Uses in-memory prefix cache for optimal performance. Fallback to default
    prefix when guild is unavailable or manager is not initialized.

    Parameters
    ----------
    bot : Tux
        The bot instance containing the prefix manager.
    message : discord.Message
        The message object containing guild context.

    Returns
    -------
    list[str]
        A list containing the resolved command prefix.
    """
    guild_id = message.guild.id if message.guild else None

    # Use prefix manager if initialized (handles override, DM, cache, and DB)
    if hasattr(bot, "prefix_manager") and bot.prefix_manager:
        prefix = await bot.prefix_manager.get_prefix(guild_id)
        return [prefix]

    # Fallback to default if prefix manager not ready
    return [CONFIG.get_prefix()]


class TuxApp:
    """
    Application wrapper for managing Tux bot lifecycle.

    This class encapsulates the setup, run, and shutdown phases of the bot,
    providing consistent signal handling, configuration validation, and
    graceful startup/shutdown orchestration.

    Attributes
    ----------
    bot : Tux | None
        The Discord bot instance, initialized in :meth:`start`.
    """

    bot: "Tux | None"

    def __init__(self) -> None:
        """Initialize the application state."""
        self.bot = None
        self._user_requested_shutdown = False
        self._background_tasks: set[asyncio.Task[Any]] = set()

    def run(self) -> int:
        """
        Run the Tux bot application.

        Synchronous entrypoint typically invoked by the CLI. Handles the
        event loop lifecycle and graceful shutdown.

        Returns
        -------
        int
            Exit code: 0 for success, 130 for user-requested shutdown, 1 for errors.
        """
        try:
            return asyncio.run(self.start())
        except KeyboardInterrupt:
            # Fallback for systems where signal handlers might not catch everything
            logger.info("Application interrupted by user")
            return 130
        except Exception as e:
            # Top-level exception handler for application startup - all exceptions should be caught
            logger.exception("Application failed to start")
            capture_exception_safe(e)
            return 1

    def _setup_signals(self) -> None:
        """Register signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()

        def _handle_signal() -> None:
            if self._user_requested_shutdown:
                return

            logger.info("Shutdown signal received - initiating graceful shutdown")
            self._user_requested_shutdown = True
            if self.bot:
                # bot.close() is a coroutine, we schedule it to stop connect()
                # Store reference to prevent garbage collection (RUF006)
                shutdown_task = loop.create_task(self.bot.close())
                self._background_tasks.add(shutdown_task)
                shutdown_task.add_done_callback(self._background_tasks.discard)

        for sig in (signal.SIGTERM, signal.SIGINT):
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, _handle_signal)

    async def start(self) -> int:
        """
        Start the Tux bot with full lifecycle management.

        Orchestrates the complete bot startup sequence: logging configuration,
        Sentry initialization, signal handler registration, configuration validation,
        bot instance creation, Discord connection, and background task monitoring.

        Returns
        -------
        int
            Exit code: 0 for success, 130 for user-requested shutdown, 1 for errors.
        """
        # Configure logging FIRST (before any other initialization)
        # This is a fallback - normally configured in scripts/tux/start.py
        # CRITICAL: Must be before SentryManager.setup() because Sentry uses logger
        from tux.core.logging import configure_logging  # noqa: PLC0415

        configure_logging(config=CONFIG)

        # Initialize telemetry (uses logger, so must be after logging config)
        SentryManager.setup()

        # Register signals
        self._setup_signals()

        # Validate token
        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set BOT_TOKEN in your .env file.")
            return 1

        # Resolve owner IDs and create bot instance
        owner_ids = self._resolve_owner_ids()
        self.bot = self._create_bot_instance(owner_ids)

        try:
            # Login and connect to Discord
            # Note: discord.py automatically calls setup_hook() during login.
            # connect() blocks until the connection is closed (e.g. via signal).
            logger.info("Logging in to Discord...")
            await self.bot.login(CONFIG.BOT_TOKEN)

            logger.info("Connecting to Discord gateway...")
            await self.bot.connect(reconnect=True)

        except Exception as e:
            logger.exception("Bot execution failed")
            capture_exception_safe(e)
            return 1
        finally:
            # Perform custom cleanup (DB, HTTP, Tasks)
            await self.shutdown()

        return self._get_exit_code()

    def _resolve_owner_ids(self) -> set[int]:
        """
        Resolve owner IDs based on configuration and eval permission settings.

        Returns
        -------
        set[int]
            Set of user IDs with owner-level permissions.
        """
        owner_ids = {CONFIG.USER_IDS.BOT_OWNER_ID}

        if CONFIG.ALLOW_SYSADMINS_EVAL:
            logger.warning("Eval is enabled for sysadmins.")
            owner_ids.update(CONFIG.USER_IDS.SYSADMINS)

        return owner_ids

    def _create_bot_instance(self, owner_ids: set[int]) -> "Tux":
        """Create and configure the Tux bot instance."""
        from tux.core.bot import Tux  # noqa: PLC0415

        return Tux(
            command_prefix=get_prefix,
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_ids=owner_ids,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
            help_command=TuxHelp(),
            status=discord.Status.online,
        )

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and flush telemetry."""
        if self.bot and not self.bot.is_closed():
            await self.bot.shutdown()

        await SentryManager.flush_async()

        logger.info(
            f"Shutdown complete (user_requested={self._user_requested_shutdown})",
        )

    def _get_exit_code(self) -> int:
        """Get the appropriate exit code based on shutdown type."""
        return 130 if self._user_requested_shutdown else 0
