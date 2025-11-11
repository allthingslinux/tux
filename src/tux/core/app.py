"""
Tux application entrypoint and lifecycle management.

This module provides the orchestration necessary to run the Tux Discord bot,
including command prefix resolution, signal handling, configuration validation,
and structured startup/shutdown flows with Sentry integration.
"""

import asyncio
import contextlib
import os
import signal
import sys
from types import FrameType
from typing import TYPE_CHECKING

import discord
from loguru import logger

from tux.help import TuxHelp
from tux.services.sentry import SentryManager, capture_exception_safe
from tux.shared.config import CONFIG

if TYPE_CHECKING:
    from tux.core.bot import Tux


async def get_prefix(bot: "Tux", message: discord.Message) -> list[str]:
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
    _in_setup : bool
        Flag indicating if we're currently in the setup phase.
    _bot_connected : bool
        Flag indicating if the bot has successfully connected to Discord.
    """

    bot: "Tux | None"
    _connect_task: asyncio.Task[None] | None
    _shutdown_event: asyncio.Event | None
    _in_setup: bool
    _bot_connected: bool

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
        self._user_requested_shutdown = False
        self._in_setup = False
        self._bot_connected = False

    def run(self) -> int:
        """
        Run the Tux bot application.

        This is the synchronous entrypoint typically invoked by the CLI.
        Creates a new event loop, runs the bot, and handles shutdown gracefully.

        Returns
        -------
        int
            Exit code: 0 for success, 130 for user-requested shutdown, 1 for errors.

        Raises
        ------
        RuntimeError
            If a critical application error occurs during startup.

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
                return loop.run_until_complete(self.start())
            finally:
                # Always close the loop to free resources, even if start() raises
                loop.close()

        except KeyboardInterrupt:
            # Ctrl+C pressed - this is a normal shutdown path
            logger.info("Application interrupted by user")
            return 130
        except RuntimeError as e:
            # Special handling for expected "Event loop stopped" errors during shutdown
            # These occur when signals force-stop the loop and are not actual errors
            if "Event loop stopped" in str(e):
                logger.debug("Event loop stopped during shutdown")
                return 130  # Likely user-initiated shutdown
            logger.error(f"Application error: {e}")
            raise
        except Exception as e:
            logger.error(f"Application error: {e}")
            capture_exception_safe(e)
            raise

    def _handle_signal_shutdown(self, loop: asyncio.AbstractEventLoop, signum: int) -> None:
        """
        Handle shutdown signal with different behavior based on bot state.

        During startup (before Discord connection), SIGINT uses immediate exit
        since synchronous operations can't be interrupted gracefully. After
        connection, uses graceful shutdown with task cancellation.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop to stop (when using graceful shutdown).
        signum : int
            The signal number received (SIGTERM or SIGINT).
        """
        # Use immediate exit for SIGINT during startup (before Discord connection)
        # to allow interrupting synchronous operations like migrations
        if signum == signal.SIGINT and not self._bot_connected:
            logger.info("SIGINT received during startup - using immediate exit")
            os._exit(1)

        # After connection, use graceful shutdown
        # Signal the shutdown monitor task to stop waiting
        logger.info("SIGINT received after connection - using graceful shutdown")
        self._user_requested_shutdown = True
        if self._shutdown_event is not None:
            self._shutdown_event.set()

        # Cancel all running async tasks to force immediate shutdown
        # This includes the bot connection task, cog tasks, etc.
        # Note: We exclude the current task to avoid cancelling ourselves
        current_task = asyncio.current_task(loop)
        for task in asyncio.all_tasks(loop):
            if not task.done() and task is not current_task:
                task.cancel()

        # Stop the event loop (will cause run_until_complete to return)
        # The actual bot shutdown will happen in the finally block of start()
        loop.call_soon_threadsafe(loop.stop)

    def setup_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Register signal handlers for graceful shutdown.

        During bot setup (which includes synchronous operations like database migrations),
        we use traditional signal handlers that can interrupt synchronous code. After setup
        completes, we switch to asyncio signal handlers for better integration.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The active event loop on which to register handlers.
        """

        # During setup, use traditional signal handlers that work with synchronous code
        def _signal_handler(signum: int, frame: FrameType | None) -> None:
            """
            Handle signals during setup - SIGINT causes immediate exit.

            Parameters
            ----------
            signum : int
                The signal number received.
            frame : FrameType, optional
                The current stack frame when the signal was received.
            """
            # For SIGINT, exit immediately
            if signum == signal.SIGINT:
                os._exit(1)
            # For other signals, raise exception
            raise KeyboardInterrupt

        # Register traditional signal handlers for setup phase
        # Remove any existing asyncio handlers first
        with contextlib.suppress(ValueError, NotImplementedError):
            loop.remove_signal_handler(signal.SIGTERM)
        with contextlib.suppress(ValueError, NotImplementedError):
            loop.remove_signal_handler(signal.SIGINT)

        # Set traditional signal handlers
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)

    def _switch_to_asyncio_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Switch from traditional signal handlers to asyncio signal handlers.

        This is called after bot setup completes, when we can rely on asyncio
        signal handlers for better integration with async operations.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop to use for signal handlers.
        """

        # Define signal handlers as closures to capture loop context
        def _sigterm() -> None:
            """Handle SIGTERM signal by initiating shutdown (graceful after connection)."""
            self._handle_signal_shutdown(loop, signal.SIGTERM)

        def _sigint() -> None:
            """Handle SIGINT signal by initiating shutdown (immediate exit during startup)."""
            self._handle_signal_shutdown(loop, signal.SIGINT)

        try:
            # Switch to asyncio signal handlers for better integration
            loop.add_signal_handler(signal.SIGTERM, _sigterm)
            loop.add_signal_handler(signal.SIGINT, _sigint)
            logger.debug("Switched to asyncio signal handlers")

        except NotImplementedError:
            # If asyncio signal handlers aren't supported, keep traditional ones
            logger.debug("Keeping traditional signal handlers (asyncio not supported)")

    async def start(self) -> int:
        """
        Start the Tux bot with full lifecycle management.

        This method orchestrates the complete bot startup sequence, including:
        - Sentry initialization for error tracking
        - Signal handler registration for graceful shutdown
        - Configuration validation and owner ID resolution
        - Bot instance creation and Discord connection
        - Background task monitoring for shutdown events

        Returns
        -------
        int
            Exit code: 0 for success, 130 for user-requested shutdown, 1 for errors.

        Notes
        -----
        The bot is not created until this method is called to ensure proper
        event loop and configuration initialization. This method will block
        until the bot disconnects or a shutdown signal is received.
        """
        # Initialize error tracking and monitoring before anything else
        SentryManager.setup()

        # Mark that we're entering setup phase (before setting up signals)
        self._in_setup = True

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

        startup_completed = False
        exit_code = 0  # Default exit code
        shutdown_code = 0  # Will be set by shutdown()
        try:
            # Login to Discord first (required before cogs can use wait_until_ready)
            logger.info("🔐 Logging in to Discord...")
            await self.bot.login(CONFIG.BOT_TOKEN)

            # Mark that bot is now connected (can handle graceful shutdown)
            self._bot_connected = True
            logger.debug("Bot connected, graceful shutdown now available")

            # Wait for bot internal setup (database, caches, etc.) after login
            await self._await_bot_setup()

            # Mark that setup is complete
            self._in_setup = False

            # After setup completes, switch to asyncio signal handlers for better performance
            self._switch_to_asyncio_signals(loop)

            # Mark startup as complete after setup succeeds
            startup_completed = True

            # Establish WebSocket connection to Discord gateway
            await self._connect_to_gateway()

        except asyncio.CancelledError:
            # Task was cancelled (likely by signal handler)
            if startup_completed:
                logger.info("Bot shutdown complete")
            else:
                logger.info("Bot startup was cancelled")
            exit_code = 130 if self._user_requested_shutdown else 0
        except KeyboardInterrupt:
            # Ctrl+C or signal handler raised KeyboardInterrupt
            logger.info("Shutdown requested (KeyboardInterrupt)")
            exit_code = 130
        except Exception as e:
            # Unexpected error during startup - log and report to Sentry
            logger.critical(f"❌ Bot failed to start: {type(e).__name__}")
            logger.info("💡 Check your configuration and ensure all services are properly set up")
            capture_exception_safe(e)
            exit_code = 1
        else:
            # Normal completion (shouldn't happen, but handle gracefully)
            exit_code = 0
        finally:
            # Always perform cleanup, regardless of how we exited
            shutdown_code = await self.shutdown()

        # Use shutdown code if available, otherwise use exception-based code
        return shutdown_code if shutdown_code != 0 else exit_code

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

    def _create_bot_instance(self, owner_ids: set[int]) -> "Tux":
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
        # Import here to avoid circular import
        from tux.core.bot import Tux  # noqa: PLC0415

        return Tux(
            command_prefix=get_prefix,
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_ids=owner_ids,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
            help_command=TuxHelp(),
            activity=None,
            status=discord.Status.online,
        )

    async def _await_bot_setup(self) -> None:
        """
        Wait for bot internal setup to complete before connecting.

        Notes
        -----
        This ensures all database connections, caches, and internal services
        are ready before attempting to connect to Discord.
        """
        logger.info("⏳️ Waiting for bot setup to complete...")

        # Ensure setup task is created and completed before connecting to Discord
        if self.bot:
            # If setup task doesn't exist yet, create it
            if self.bot.setup_task is None:
                logger.debug("Setup task not created yet, creating it now")
                self.bot.create_setup_task()

            # Wait for setup to complete
            if self.bot.setup_task:
                await self.bot.setup_task
                logger.info("✅ Bot setup completed successfully")

    async def _connect_to_gateway(self) -> None:
        """
        Establish WebSocket connection to Discord gateway with reconnection support.

        This method creates background tasks for the Discord connection and
        shutdown monitoring, waiting for either to complete.

        Notes
        -----
        The bot must already be logged in before calling this method.
        Uses connect() call with auto-reconnect and proper task coordination
        for graceful shutdown.
        """
        if not self.bot:
            return

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

    async def shutdown(self) -> int:
        """
        Gracefully shut down the bot and flush telemetry.

        This method ensures proper cleanup of all bot resources, including
        closing the Discord connection and flushing any pending Sentry events.

        Returns
        -------
        int
            Exit code: 130 if user requested shutdown, 0 otherwise.

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

        logger.info(f"Shutdown complete (user_requested={self._user_requested_shutdown})")
        if self._user_requested_shutdown:
            logger.info("Exiting with code 130 (user requested shutdown)")
            return 130
        logger.info("Shutdown completed normally")
        return 0
