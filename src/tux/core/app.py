"""
Tux application entrypoint and lifecycle management.

This module provides the orchestration necessary to run the Tux Discord bot,
including command prefix resolution, signal handling, configuration validation,
and structured startup/shutdown flows with Sentry integration.
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
from tux.services.sentry import SentryManager, capture_exception_safe
from tux.shared.config import CONFIG


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """
    Resolve the command prefix for a guild using the prefix manager.

    This function uses the in-memory prefix cache for optimal performance,
    falling back to the default prefix when the guild is unavailable. If
    BOT_INFO__PREFIX is set in environment variables, all guilds will use
    that prefix, ignoring database settings.

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

    Notes
    -----
    Prefix resolution follows this priority order:
    1. Environment variable override (BOT_INFO__PREFIX)
    2. Guild-specific prefix from prefix manager cache
    3. Default prefix from configuration
    """
    # Priority 1: Environment variable override for testing/development
    if CONFIG.is_prefix_override_enabled():
        return [CONFIG.get_prefix()]

    # Priority 2: DM channels always use default prefix (no guild context)
    if not message.guild:
        return [CONFIG.get_prefix()]

    # Priority 3: Guild-specific prefix from cached database value
    # Using hasattr check to handle early initialization before prefix_manager is ready
    if hasattr(bot, "prefix_manager") and bot.prefix_manager:
        prefix = await bot.prefix_manager.get_prefix(message.guild.id)
        return [prefix]

    # Priority 4: Fallback to default if prefix manager not ready
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
    _connect_task : asyncio.Task[None] | None
        Background task for the Discord connection.
    _shutdown_event : asyncio.Event | None
        Event flag for coordinating graceful shutdown.
    """

    bot: Tux | None
    _connect_task: asyncio.Task[None] | None
    _shutdown_event: asyncio.Event | None

    def __init__(self) -> None:
        """
        Initialize the application state.

        Notes
        -----
        The bot instance is not created until :meth:`start` to ensure the
        event loop and configuration are properly initialized.
        """
        self.bot = None
        self._connect_task = None
        self._shutdown_event = None

    def run(self) -> None:
        """
        Run the Tux bot application.

        This is the synchronous entrypoint typically invoked by the CLI.
        Creates a new event loop, runs the bot, and handles shutdown gracefully.

        Raises
        ------
        RuntimeError
            If a critical application error occurs during startup.
        Exception
            Any unexpected errors are logged to Sentry and re-raised.

        Notes
        -----
        This method handles KeyboardInterrupt gracefully and ensures the
        event loop is properly closed regardless of how the application exits.
        """
        try:
            # Create a fresh event loop for this application run
            # This ensures clean state and avoids conflicts with any existing loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Block until the bot disconnects or shutdown is requested
                loop.run_until_complete(self.start())
            finally:
                # Always close the loop to free resources, even if start() raises
                loop.close()

        except KeyboardInterrupt:
            # Ctrl+C pressed - this is a normal shutdown path
            logger.info("Application interrupted by user")
        except RuntimeError as e:
            # Special handling for expected "Event loop stopped" errors during shutdown
            # These occur when signals force-stop the loop and are not actual errors
            if "Event loop stopped" in str(e):
                logger.debug("Event loop stopped during shutdown")
            else:
                logger.error(f"Application error: {e}")
                raise
        except Exception as e:
            logger.error(f"Application error: {e}")
            capture_exception_safe(e)
            raise

    def _handle_signal_shutdown(self, loop: asyncio.AbstractEventLoop, signum: int) -> None:
        """
        Handle shutdown signal by canceling tasks and stopping the event loop.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop to stop.
        signum : int
            The signal number received (SIGTERM or SIGINT).
        """
        # Report signal to Sentry for monitoring/debugging
        SentryManager.report_signal(signum, None)
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info(f"{signal_name} received, forcing shutdown...")

        # Signal the shutdown monitor task to stop waiting
        if self._shutdown_event is not None:
            self._shutdown_event.set()

        # Cancel all running async tasks to force immediate shutdown
        # This includes the bot connection task, cog tasks, etc.
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()

        # Attempt to close the Discord connection gracefully
        # Create a task but don't await it (signal handlers can't be async)
        if self.bot and not self.bot.is_closed():
            close_task = asyncio.create_task(self.bot.close())
            _ = close_task  # Store reference to prevent garbage collection

        # Stop the event loop (will cause run_until_complete to return)
        loop.call_soon_threadsafe(loop.stop)

    def setup_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Register signal handlers for graceful shutdown.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The active event loop on which to register handlers.

        Notes
        -----
        Uses ``loop.add_signal_handler`` where available, falling back to the
        ``signal`` module on platforms that do not support it (e.g., Windows).

        On Windows, signal handling is limited and may not work as expected
        for all signal types.
        """

        # Define signal handlers as closures to capture loop context
        def _sigterm() -> None:
            """Handle SIGTERM signal by initiating graceful shutdown."""
            self._handle_signal_shutdown(loop, signal.SIGTERM)

        def _sigint() -> None:
            """Handle SIGINT signal by initiating graceful shutdown."""
            self._handle_signal_shutdown(loop, signal.SIGINT)

        try:
            # Preferred method: Register handlers directly on the event loop
            # This is more reliable and integrates better with asyncio
            loop.add_signal_handler(signal.SIGTERM, _sigterm)
            loop.add_signal_handler(signal.SIGINT, _sigint)

        except NotImplementedError:
            # Fallback for Windows: Use traditional signal module
            # This doesn't integrate as well with asyncio but is the only option
            def _signal_handler(signum: int, frame: FrameType | None) -> None:
                """Handle signals on Windows by reporting to Sentry and raising KeyboardInterrupt.

                Parameters
                ----------
                signum : int
                    The signal number received.
                frame : FrameType, optional
                    The current stack frame when the signal was received.
                """
                SentryManager.report_signal(signum, frame)
                logger.info(f"Signal {signum} received, shutting down...")
                # Raise KeyboardInterrupt to break out of run_until_complete
                raise KeyboardInterrupt

            signal.signal(signal.SIGTERM, _signal_handler)
            signal.signal(signal.SIGINT, _signal_handler)

        # Warn users on Windows about signal handling limitations
        if sys.platform.startswith("win"):
            logger.warning(
                "Signal handling is limited on Windows. Some signals may not be handled as expected.",
            )

    async def start(self) -> None:
        """
        Start the Tux bot with full lifecycle management.

        This method orchestrates the complete bot startup sequence, including:
        - Sentry initialization for error tracking
        - Signal handler registration for graceful shutdown
        - Configuration validation and owner ID resolution
        - Bot instance creation and Discord connection
        - Background task monitoring for shutdown events

        Raises
        ------
        SystemExit
            If BOT_TOKEN is not configured in the environment.
        Exception
            Any errors during bot setup or connection are logged to Sentry.

        Notes
        -----
        The bot is not created until this method is called to ensure proper
        event loop and configuration initialization. This method will block
        until the bot disconnects or a shutdown signal is received.
        """
        # Initialize error tracking and monitoring before anything else
        SentryManager.setup()

        # Register signal handlers for graceful shutdown (SIGTERM, SIGINT)
        loop = asyncio.get_running_loop()
        self.setup_signals(loop)

        # Validate that the bot token is configured before attempting connection
        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set BOT_TOKEN in your .env file.")
            sys.exit(1)

        # Resolve owner IDs and create the bot instance
        owner_ids = self._resolve_owner_ids()
        self.bot = self._create_bot_instance(owner_ids)

        try:
            # Wait for bot internal setup (database, caches, etc.) before connecting
            await self._await_bot_setup()

            # Connect to Discord and wait for disconnect or shutdown signal
            await self._login_and_connect()

        except asyncio.CancelledError:
            # Task was cancelled (likely by signal handler) - normal shutdown path
            logger.info("Bot startup was cancelled")
        except KeyboardInterrupt:
            # Ctrl+C or signal handler raised KeyboardInterrupt
            logger.info("Shutdown requested (KeyboardInterrupt)")
        except Exception as e:
            # Unexpected error during startup - log and report to Sentry
            logger.critical(f"❌ Bot failed to start: {type(e).__name__}")
            logger.info("💡 Check your configuration and ensure all services are properly set up")
            capture_exception_safe(e)
        finally:
            # Always perform cleanup, regardless of how we exited
            await self.shutdown()

    def _resolve_owner_ids(self) -> set[int]:
        """
        Resolve owner IDs based on configuration and eval permission settings.

        Returns
        -------
        set[int]
            Set of user IDs with owner-level permissions.

        Notes
        -----
        If ALLOW_SYSADMINS_EVAL is enabled, sysadmin IDs are added to the
        owner set, granting them eval command access.
        """
        # Start with the bot owner (always has owner permissions)
        owner_ids = {CONFIG.USER_IDS.BOT_OWNER_ID}

        # Optionally grant sysadmins eval access (dangerous but useful for debugging)
        if CONFIG.ALLOW_SYSADMINS_EVAL:
            logger.warning(
                "⚠️ Eval is enabled for sysadmins, this is potentially dangerous; see .env file for more info.",
            )
            owner_ids.update(CONFIG.USER_IDS.SYSADMINS)
        else:
            logger.warning("🔒️ Eval is disabled for sysadmins; see .env file for more info.")

        return owner_ids

    def _create_bot_instance(self, owner_ids: set[int]) -> Tux:
        """
        Create and configure the Tux bot instance.

        Parameters
        ----------
        owner_ids : set[int]
            Set of user IDs with owner-level permissions.

        Returns
        -------
        Tux
            Configured bot instance ready for connection.
        """
        return Tux(
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

    async def _await_bot_setup(self) -> None:
        """
        Wait for bot internal setup to complete before connecting.

        Raises
        ------
        Exception
            If bot setup fails, the exception is logged to Sentry and re-raised.

        Notes
        -----
        This ensures all database connections, caches, and internal services
        are ready before attempting to connect to Discord.
        """
        logger.info("⏳️ Waiting for bot setup to complete...")

        # The bot creates a setup_task in __init__ that handles async initialization
        # This includes database connections, loading cogs, initializing caches, etc.
        if self.bot and self.bot.setup_task:
            try:
                await self.bot.setup_task
                logger.info("✅ Bot setup completed successfully")
            except Exception as setup_error:
                # Setup failure is critical - can't proceed without database, cogs, etc.
                logger.error(f"❌ Bot setup failed: {setup_error}")
                capture_exception_safe(setup_error)
                raise

    async def _login_and_connect(self) -> None:
        """
        Login to Discord and establish connection with reconnection support.

        This method creates background tasks for the Discord connection and
        shutdown monitoring, waiting for either to complete.

        Notes
        -----
        Uses separate login() and connect() calls to avoid blocking and
        enable proper task coordination for graceful shutdown.
        """
        if not self.bot:
            return

        # Authenticate with Discord API (validates token, retrieves bot user info)
        logger.info("🔐 Logging in to Discord...")
        await self.bot.login(CONFIG.BOT_TOKEN)

        # Establish WebSocket connection to Discord gateway
        logger.info("🌐 Connecting to Discord...")
        self._connect_task = asyncio.create_task(
            self.bot.connect(reconnect=True),  # Auto-reconnect on disconnections
            name="bot_connect",
        )

        # Create monitor task to watch for shutdown signals concurrently
        shutdown_task = asyncio.create_task(
            self._monitor_shutdown(),
            name="shutdown_monitor",
        )

        # Wait for either connection to end or shutdown to be requested
        # FIRST_COMPLETED ensures we react immediately to whichever happens first
        _, pending = await asyncio.wait(
            [self._connect_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel the task that didn't complete (either connection or monitor)
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _monitor_shutdown(self) -> None:
        """
        Monitor for shutdown signals while the bot is running.

        This method creates and waits on a shutdown event that is set by
        signal handlers when a termination signal is received.

        Notes
        -----
        This task runs concurrently with the bot connection task and will
        trigger shutdown when a signal is received.
        """
        # Create an event flag that signal handlers can set
        self._shutdown_event = asyncio.Event()

        # Block here until the event is set (by signal handler or other shutdown trigger)
        await self._shutdown_event.wait()

        logger.info("Shutdown requested via monitor")

    async def shutdown(self) -> None:
        """
        Gracefully shut down the bot and flush telemetry.

        This method ensures proper cleanup of all bot resources, including
        closing the Discord connection and flushing any pending Sentry events.

        Notes
        -----
        This method is called automatically in the finally block of :meth:`start`,
        ensuring cleanup occurs regardless of how the application exits.
        """
        # Close the Discord WebSocket connection and cleanup bot resources
        # (database connections, HTTP sessions, background tasks, etc.)
        if self.bot and not self.bot.is_closed():
            await self.bot.shutdown()

        # Flush any pending Sentry events before exiting
        # This ensures error reports aren't lost during shutdown
        await SentryManager.flush_async()

        logger.info("Shutdown complete")
