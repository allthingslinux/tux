"""Tux Discord bot core implementation.

Defines the Tux bot class, which extends discord.py's Bot and manages
setup, cog loading, error handling, and resource cleanup.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any, cast

import discord
from discord.ext import commands
from loguru import logger
from rich.console import Console

from tux.core.cog_loader import CogLoader
from tux.core.container import ServiceContainer
from tux.core.service_registry import ServiceRegistry
from tux.core.task_monitor import TaskMonitor
from tux.database.migrations.runner import upgrade_head_if_needed
from tux.database.service import DatabaseService
from tux.services.emoji_manager import EmojiManager
from tux.services.sentry_manager import SentryManager
from tux.services.tracing import (
    capture_exception_safe,
    instrument_bot_commands,
    set_setup_phase_tag,
    set_span_error,
    start_span,
    start_transaction,
)
from tux.shared.config import CONFIG
from tux.ui.banner import create_banner

# Re-export the T type for backward compatibility
__all__ = ["ContainerInitializationError", "DatabaseConnectionError", "Tux"]


class DatabaseConnectionError(RuntimeError):
    """Raised when database connection fails."""

    CONNECTION_FAILED = "Failed to establish database connection"


class ContainerInitializationError(RuntimeError):
    """Raised when dependency injection container initialization fails."""

    INITIALIZATION_FAILED = "Failed to initialize dependency injection container"


class Tux(commands.Bot):
    """Main bot class for Tux, extending ``discord.py``'s ``commands.Bot``.

    Responsibilities
    ----------------
    - Connect to the database and validate readiness
    - Initialize the DI container and load cogs/extensions
    - Configure Sentry tracing and enrich spans
    - Start background task monitoring and perform graceful shutdown
    """

    # Error message constants
    _DB_SERVICE_UNAVAILABLE = "Database service not available in container"
    _DB_CONNECTION_TEST_FAILED = "Database connection test failed"
    _CONTAINER_VALIDATION_FAILED = "Container validation failed - missing required services"
    _CONTAINER_NOT_INITIALIZED = "Container is not initialized"
    _CONTAINER_VALIDATION_FAILED_GENERIC = "Container validation failed"

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
        # Dependency injection container
        self.container: ServiceContainer | None = None
        # Sentry manager instance for error handling and context utilities
        self.sentry_manager: SentryManager = SentryManager()
        # Prefix manager for efficient prefix resolution
        self.prefix_manager: Any | None = None

        # UI / misc
        self.emoji_manager = EmojiManager(self)
        self.console = Console(stderr=True, force_terminal=True)
        self.uptime = discord.utils.utcnow().timestamp()

        logger.debug("Creating bot setup task")
        self.setup_task = asyncio.create_task(self.setup(), name="bot_setup")
        # Remove callback to prevent exception re-raising
        # Task completion will be handled in setup_hook instead

    async def setup(self) -> None:  # noqa: PLR0912, PLR0915
        """Perform one-time bot setup.

        Steps
        -----
        - Connect to the database and validate connection
        - Initialize and validate DI container
        - Load extensions and cogs
        - Initialize hot reload (if enabled)
        - Start background task monitoring
        """
        try:
            # High-level setup pipeline with tracing
            with start_span("bot.setup", "Bot setup process") as span:
                set_setup_phase_tag(span, "starting")
                await self._setup_container()
                set_setup_phase_tag(span, "container", "finished")
                await self._setup_database()
                # Ensure DB schema is up-to-date in non-dev
                try:
                    await upgrade_head_if_needed()
                except RuntimeError as e:
                    # Migration failed with a clean error message
                    if "Database connection failed during migrations" in str(e):
                        db_migration_error = "Database connection failed during migrations"
                        raise DatabaseConnectionError(db_migration_error) from e
                    raise
                except Exception as e:
                    # Other migration errors
                    if "connection failed" in str(e) or "Connection refused" in str(e):
                        db_migration_error = "Database connection failed during migrations"
                        raise DatabaseConnectionError(db_migration_error) from e
                    raise
                set_setup_phase_tag(span, "database", "finished")
                await self._setup_prefix_manager()
                set_setup_phase_tag(span, "prefix_manager", "finished")
                await self._load_drop_in_extensions()
                set_setup_phase_tag(span, "extensions", "finished")
                await self._load_cogs()
                set_setup_phase_tag(span, "cogs", "finished")
                await self._setup_hot_reload()
                set_setup_phase_tag(span, "hot_reload", "finished")
                self.task_monitor.start()
                set_setup_phase_tag(span, "monitoring", "finished")

        except DatabaseConnectionError as e:
            logger.error("❌ Database connection failed")
            logger.info("💡 To start the database, run: make docker-up")
            logger.info("   Or start just PostgreSQL: docker compose up tux-postgres -d")

            if self.sentry_manager.is_initialized:
                self.sentry_manager.set_context("setup_failure", {"error": str(e), "error_type": "database_connection"})
            capture_exception_safe(e)

            # Don't call shutdown here - let main function handle it to avoid recursion
            # Let the main function handle the exit
            error_msg = "Database setup failed"
            raise RuntimeError(error_msg) from e

        except ContainerInitializationError as e:
            logger.error("❌ Dependency injection container failed to initialize")
            logger.info("💡 Check your configuration and service registrations")

            if self.sentry_manager.is_initialized:
                self.sentry_manager.set_context(
                    "setup_failure",
                    {"error": str(e), "error_type": "container_initialization"},
                )
            capture_exception_safe(e)

            # Don't call shutdown here - let main function handle it to avoid recursion
            # Let the main function handle the exit
            error_msg = "Container setup failed"
            raise RuntimeError(error_msg) from e

        except Exception as e:
            # Check if this is a database connection error that we haven't caught yet
            if "connection failed" in str(e) or "Connection refused" in str(e):
                logger.error("❌ Database connection failed")
                logger.info("💡 To start the database, run: make docker-up")
                logger.info("   Or start just PostgreSQL: docker compose up tux-postgres -d")
            else:
                logger.error(f"❌ Critical error during setup: {type(e).__name__}: {e}")
                logger.info("💡 Check the logs above for more details")

            if self.sentry_manager.is_initialized:
                self.sentry_manager.set_context("setup_failure", {"error": str(e), "error_type": type(e).__name__})
            capture_exception_safe(e)

            # Don't call shutdown here - let main function handle it to avoid recursion
            # Let the main function handle the exit
            error_msg = "Bot setup failed"
            raise RuntimeError(error_msg) from e

        except BaseException as e:
            # Catch any remaining exceptions (including KeyboardInterrupt, SystemExit)
            # Let the main function handle the exit
            error_msg = "Bot setup failed with critical error"
            raise RuntimeError(error_msg) from e

    async def _setup_database(self) -> None:
        """Set up and validate the database connection."""
        with start_span("bot.database_connect", "Setting up database connection") as span:
            logger.info("🔌 Connecting to database...")

            def _raise_db_error(message: str) -> None:
                """Raise database connection error with given message."""
                raise DatabaseConnectionError(message)

            try:
                # Prefer DI service; fall back to shared client early in startup
                db_service = self.container.get_optional(DatabaseService) if self.container else None
                if db_service is None:
                    _raise_db_error(self._DB_SERVICE_UNAVAILABLE)

                # Narrow type for type checker
                db_service = cast(DatabaseService, db_service)
                await db_service.connect(CONFIG.database_url)
                connected = db_service.is_connected()

                if not connected:
                    _raise_db_error(self._DB_CONNECTION_TEST_FAILED)

                # Minimal telemetry for connection health
                span.set_tag("db.connected", connected)
                logger.info("✅ Database connected successfully")

                # Create tables if they don't exist (for development/production)
                # This ensures the schema is available even if migrations are incomplete
                try:
                    from sqlmodel import SQLModel  # noqa: PLC0415

                    # Get the underlying SQLAlchemy engine
                    engine = db_service.engine
                    if engine:
                        # Create tables using SQLAlchemy metadata
                        logger.info("🏗️  Creating database tables...")
                        if hasattr(engine, "begin"):  # Async engine
                            async with engine.begin() as conn:
                                await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
                        else:  # Sync engine
                            SQLModel.metadata.create_all(engine, checkfirst=True)
                        logger.info("✅ Database tables created/verified")
                except Exception as table_error:
                    logger.warning(f"⚠️  Table creation failed (may already exist): {table_error}")
                    # Don't fail the startup for table creation issues

            except Exception as e:
                set_span_error(span, e, "db_error")

                if isinstance(e, DatabaseConnectionError):
                    raise

                # Wrap other database errors
                error_msg = f"Database connection failed: {e}"
                raise DatabaseConnectionError(error_msg) from e

    async def _setup_container(self) -> None:
        """Set up and configure the dependency injection container."""
        with start_span("bot.container_setup", "Setting up dependency injection container") as span:
            logger.info("🔧 Initializing dependency injection container...")

            def _raise_container_error(message: str) -> None:
                """Raise container initialization error with given message."""
                raise ContainerInitializationError(message)

            try:
                # Configure the service container with all required services
                self.container = ServiceRegistry.configure_container(self)

                # Validate that all required services are registered
                if not ServiceRegistry.validate_container(self.container):
                    error_msg = self._CONTAINER_VALIDATION_FAILED
                    logger.error(f"❌ {error_msg}")
                    _raise_container_error(error_msg)

                # Log registered services for debugging/observability
                registered_services = ServiceRegistry.get_registered_services(self.container)
                logger.info(f"✅ Container initialized with {len(registered_services)} services")

                span.set_tag("container.initialized", True)
                span.set_tag("container.services_count", len(registered_services))
                span.set_data("container.services", registered_services)

            except Exception as e:
                set_span_error(span, e, "container_error")

                if isinstance(e, ContainerInitializationError):
                    raise

                # Wrap other container errors
                error_msg = f"Container initialization failed: {e}"
                raise ContainerInitializationError(error_msg) from e

    async def _setup_prefix_manager(self) -> None:
        """Set up the prefix manager for efficient prefix resolution."""
        with start_span("bot.setup_prefix_manager", "Setting up prefix manager") as span:
            logger.info("🔧 Initializing prefix manager...")

            try:
                # Import here to avoid circular imports
                from tux.core.prefix_manager import PrefixManager  # noqa: PLC0415

                # Initialize the prefix manager
                self.prefix_manager = PrefixManager(self)

                # Load all existing prefixes into cache with timeout
                await asyncio.wait_for(
                    self.prefix_manager.load_all_prefixes(),
                    timeout=15.0,  # 15 second timeout for the entire setup
                )

                span.set_tag("prefix_manager.initialized", True)
                logger.info("✅ Prefix manager initialized successfully")

            except TimeoutError:
                logger.warning("⚠️  Prefix manager setup timed out - continuing without cache")
                span.set_tag("prefix_manager.initialized", False)
                span.set_data("error", "timeout")
                self.prefix_manager = None
            except Exception as e:
                logger.error(f"❌ Failed to initialize prefix manager: {type(e).__name__}: {e}")
                span.set_tag("prefix_manager.initialized", False)
                span.set_data("error", str(e))

                # Don't fail startup if prefix manager fails - bot can still work with default prefix
                logger.warning("⚠️  Bot will use default prefix for all guilds")
                self.prefix_manager = None

    async def _load_drop_in_extensions(self) -> None:
        """Load optional drop-in extensions (e.g., Jishaku)."""
        with start_span("bot.load_drop_in_extensions", "Loading drop-in extensions") as span:
            try:
                await self.load_extension("jishaku")
                logger.info("✅ Jishaku extension loaded")
                span.set_tag("jishaku.loaded", True)

            except commands.ExtensionError as e:
                logger.warning(f"⚠️  Jishaku extension not loaded: {e}")
                span.set_tag("jishaku.loaded", False)
                span.set_data("error", str(e))

    @staticmethod
    def _validate_db_connection() -> None:
        return None

    def _validate_container(self) -> None:
        """Raise if the dependency injection container is not properly initialized."""
        # Ensure container object exists before attempting to use it
        if self.container is None:
            error_msg = self._CONTAINER_NOT_INITIALIZED
            raise ContainerInitializationError(error_msg)

        # Validate registered services and basic invariants via the registry
        if not ServiceRegistry.validate_container(self.container):
            error_msg = self._CONTAINER_VALIDATION_FAILED_GENERIC
            raise ContainerInitializationError(error_msg)

    def _raise_container_validation_error(self, message: str) -> None:
        """Helper method to raise container validation errors."""
        raise ContainerInitializationError(message)

    async def setup_hook(self) -> None:
        """One-time async setup before connecting to Discord (``discord.py`` hook)."""
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
                    if self.container:
                        registered_services = ServiceRegistry.get_registered_services(self.container)
                        self.sentry_manager.set_context(
                            "container_info",
                            {
                                "initialized": True,
                                "services_count": len(registered_services),
                                "services": registered_services,
                            },
                        )

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
        await self._wait_for_setup()
        await self._set_presence()

    async def _set_presence(self) -> None:
        """Set the bot's presence (activity and status)."""
        activity = discord.Activity(type=discord.ActivityType.watching, name="for /help")
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

            self._cleanup_container()
            transaction.set_tag("container_cleaned", True)

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
                # Database connection via DI when available
                logger.debug("Closing database connections")

                db_service = self.container.get(DatabaseService) if self.container else None
                if db_service is not None:
                    await db_service.disconnect()
                logger.debug("Database connections closed")
                span.set_tag("db_closed", True)

            except Exception as e:
                logger.error(f"⚠️  Error during database disconnection: {e}")
                span.set_tag("db_closed", False)
                span.set_data("db_error", str(e))

                capture_exception_safe(e)

    def _cleanup_container(self) -> None:
        """Clean up the dependency injection container."""
        with start_span("bot.cleanup_container", "Cleaning up dependency injection container"):
            if self.container is not None:
                logger.debug("Cleaning up dependency injection container")
                # The container doesn't need explicit cleanup, just clear the reference
                self.container = None
                logger.debug("Dependency injection container cleaned up")

    async def _load_cogs(self) -> None:
        """Load bot cogs using CogLoader."""
        with start_span("bot.load_cogs", "Loading all cogs") as span:
            logger.info("🔧 Loading cogs...")

            try:
                await CogLoader.setup(self)
                span.set_tag("cogs_loaded", True)

                # Load Sentry handler cog to enrich spans and handle command errors
                sentry_ext = "tux.services.handlers.sentry"
                if sentry_ext not in self.extensions:
                    try:
                        await self.load_extension(sentry_ext)
                        span.set_tag("sentry_handler.loaded", True)
                    except Exception as sentry_err:
                        logger.warning(f"⚠️  Failed to load Sentry handler: {sentry_err}")
                        span.set_tag("sentry_handler.loaded", False)
                        capture_exception_safe(sentry_err)
                else:
                    span.set_tag("sentry_handler.loaded", True)

            except Exception as e:
                logger.error(f"❌ Error loading cogs: {type(e).__name__}: {e}")
                span.set_tag("cogs_loaded", False)
                span.set_data("error", str(e))

                capture_exception_safe(e)
                raise

    async def _log_startup_banner(self) -> None:
        """Log bot startup information (banner, stats, etc.)."""
        with start_span("bot.log_banner", "Displaying startup banner"):
            banner = create_banner(
                bot_name=CONFIG.BOT_INFO.BOT_NAME,
                version=CONFIG.BOT_INFO.BOT_VERSION,
                bot_id=str(self.user.id) if self.user else None,
                guild_count=len(self.guilds),
                user_count=len(self.users),
                prefix=CONFIG.get_prefix(),
            )

            self.console.print(banner)

    async def _setup_hot_reload(self) -> None:
        """Set up hot reload system after all cogs are loaded."""
        if not self._hot_reload_loaded and "tux.services.hot_reload" not in self.extensions:
            with start_span("bot.setup_hot_reload", "Setting up hot reload system"):
                try:
                    await self.load_extension("tux.services.hot_reload")
                    self._hot_reload_loaded = True
                    logger.info("🔥 Hot reload system initialized")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load hot reload extension: {e}")
                    capture_exception_safe(e)
