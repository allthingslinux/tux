"""Tux application entrypoint and lifecycle utilities.

This module provides the orchestration necessary to run the Tux Discord bot,
including:

- Command prefix resolution based on per-guild configuration
- Signal handling for graceful shutdown
- Validation of runtime configuration
- Structured startup/shutdown flow with Sentry integration
"""

import asyncio
import contextlib
import signal
import sys
from types import FrameType

import discord
from loguru import logger

from tux.core.bot import Tux
from tux.help import TuxHelp
from tux.services.sentry_manager import SentryManager
from tux.shared.config import CONFIG


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Get the command prefix for a guild using the prefix manager.

    This function uses the in-memory prefix cache for optimal performance,
    falling back to the default prefix when the guild is unavailable.

    If BOT_INFO__PREFIX is set in environment variables, all guilds will use
    that prefix, ignoring database settings.
    """
    # Check if prefix override is enabled by environment variable
    if CONFIG.is_prefix_override_enabled():
        return [CONFIG.get_prefix()]

    if not message.guild:
        return [CONFIG.get_prefix()]

    # Use the prefix manager for efficient prefix resolution
    if hasattr(bot, "prefix_manager") and bot.prefix_manager:
        prefix = await bot.prefix_manager.get_prefix(message.guild.id)
        return [prefix]

    # Fallback to default prefix if prefix manager is not available
    return [CONFIG.get_prefix()]


class TuxApp:
    """Application wrapper that manages Tux bot lifecycle.

    This class encapsulates setup, run, and shutdown phases of the bot,
    providing consistent signal handling and configuration validation.
    """

    def __init__(self):
        """Initialize the application state.

        Notes
        -----
        The bot instance is not created until :meth:`start` to ensure the
        event loop and configuration are ready.
        """
        self.bot: Tux | None = None

    def run(self) -> None:
        """Run the Tux bot application.

        This is the synchronous entrypoint typically invoked by the CLI.
        """
        try:
            # Use a more direct approach to handle signals
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the bot with the event loop
                loop.run_until_complete(self.start())
            finally:
                loop.close()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except RuntimeError as e:
            # Handle event loop stopped errors gracefully (these are expected during shutdown)
            if "Event loop stopped" in str(e):
                logger.debug("Event loop stopped during shutdown")
            else:
                logger.error(f"Application error: {e}")
                raise
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise

    def setup_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register signal handlers for graceful shutdown.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The active event loop on which to register handlers.

        Notes
        -----
        Uses ``loop.add_signal_handler`` where available, falling back to the
        ``signal`` module on platforms that do not support it (e.g. Windows).
        """

        def _sigterm() -> None:
            SentryManager.report_signal(signal.SIGTERM, None)
            logger.info("SIGTERM received, forcing shutdown...")
            # Set shutdown event for the monitor
            if hasattr(self, "_shutdown_event"):
                self._shutdown_event.set()
            # Cancel ALL tasks in the event loop
            for task in asyncio.all_tasks(loop):
                if not task.done():
                    task.cancel()
            # Force close the bot connection if it exists
            if hasattr(self, "bot") and self.bot and not self.bot.is_closed():
                close_task = asyncio.create_task(self.bot.close())
                # Store reference to prevent garbage collection
                _ = close_task
            # Stop the event loop
            loop.call_soon_threadsafe(loop.stop)

        def _sigint() -> None:
            SentryManager.report_signal(signal.SIGINT, None)
            logger.info("SIGINT received, forcing shutdown...")
            # Set shutdown event for the monitor
            if hasattr(self, "_shutdown_event"):
                self._shutdown_event.set()
            # Cancel ALL tasks in the event loop
            for task in asyncio.all_tasks(loop):
                if not task.done():
                    task.cancel()
            # Force close the bot connection if it exists
            if hasattr(self, "bot") and self.bot and not self.bot.is_closed():
                close_task = asyncio.create_task(self.bot.close())
                # Store reference to prevent garbage collection
                _ = close_task
            # Stop the event loop
            loop.call_soon_threadsafe(loop.stop)

        try:
            loop.add_signal_handler(signal.SIGTERM, _sigterm)
            loop.add_signal_handler(signal.SIGINT, _sigint)

        except NotImplementedError:
            # Fallback for platforms that do not support add_signal_handler (e.g., Windows)
            def _signal_handler(signum: int, frame: FrameType | None) -> None:
                SentryManager.report_signal(signum, frame)
                logger.info(f"Signal {signum} received, shutting down...")
                # For Windows fallback, raise KeyboardInterrupt to stop the event loop
                raise KeyboardInterrupt

            signal.signal(signal.SIGTERM, _signal_handler)
            signal.signal(signal.SIGINT, _signal_handler)

        if sys.platform.startswith("win"):
            logger.warning(
                "Warning: Signal handling is limited on Windows. Some signals may not be handled as expected.",
            )

    async def start(self) -> None:
        """Start the Tux bot, managing setup and error handling.

        This method initializes Sentry, registers signal handlers, validates
        configuration, constructs the bot, and begins the Discord connection.
        """

        # Initialize Sentry via façade
        SentryManager.setup()

        # Setup signals via event loop
        loop = asyncio.get_running_loop()
        self.setup_signals(loop)

        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set BOT_TOKEN in your .env file.")
            sys.exit(1)

        owner_ids = {CONFIG.USER_IDS.BOT_OWNER_ID}

        if CONFIG.ALLOW_SYSADMINS_EVAL:
            logger.warning(
                "⚠️ Eval is enabled for sysadmins, this is potentially dangerous; see .env file for more info.",
            )
            owner_ids.update(CONFIG.USER_IDS.SYSADMINS)
        else:
            logger.warning("🔒️ Eval is disabled for sysadmins; see .env file for more info.")

        self.bot = Tux(
            command_prefix=get_prefix,
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_ids=owner_ids,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            help_command=TuxHelp(),
            activity=None,
            status=discord.Status.online,
        )

        try:
            # Use login() + connect() separately to avoid blocking
            logger.info("🔐 Logging in to Discord...")
            await self.bot.login(CONFIG.BOT_TOKEN)

            logger.info("🌐 Connecting to Discord...")
            # Create a task for the connection
            self._connect_task = asyncio.create_task(self.bot.connect(reconnect=True), name="bot_connect")

            # Create a task to monitor for shutdown signals
            shutdown_task = asyncio.create_task(self._monitor_shutdown(), name="shutdown_monitor")

            # Wait for either the connection to complete or shutdown to be requested
            done, pending = await asyncio.wait([self._connect_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED)

            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        except asyncio.CancelledError:
            # Handle cancellation gracefully
            logger.info("Bot startup was cancelled")
        except KeyboardInterrupt:
            logger.info("Shutdown requested (KeyboardInterrupt)")
        except Exception as e:
            logger.critical(f"❌ Bot failed to start: {type(e).__name__}")
            logger.info("💡 Check your configuration and ensure all services are properly set up")
        finally:
            await self.shutdown()

    async def _monitor_shutdown(self) -> None:
        """Monitor for shutdown signals while the bot is running."""
        # Create an event to track shutdown requests
        self._shutdown_event = asyncio.Event()

        # Wait for shutdown event
        await self._shutdown_event.wait()

        logger.info("Shutdown requested via monitor")

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and flush telemetry.

        Ensures the bot client is closed and Sentry is flushed asynchronously
        before returning.
        """

        if self.bot and not self.bot.is_closed():
            await self.bot.shutdown()

        await SentryManager.flush_async()

        logger.info("Shutdown complete")
