"""
Unified Database Service - Professional Architecture

This module provides the ONLY database service for the application.
It handles both SQLAlchemy session management AND controller access.

Architecture:
- DatabaseService: Session management + controller access (THIS FILE)
- DatabaseCoordinator: Coordinates access to all controllers
- Controllers: Business logic per model (AFK, Guild, etc.)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, TypeVar

import sentry_sdk
import sqlalchemy.exc
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

import tux.database.models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from tux.shared.config.env import get_database_url

T = TypeVar("T")


class DatabaseService:
    """
    Unified Database Service - handles both connections AND controller access.

    This is the ONLY database service in the application.
    Provides:
    - SQLAlchemy session management
    - Connection pooling
    - Transaction management
    - Direct access to all controllers

    Professional singleton pattern with lazy loading.
    """

    _instance: DatabaseService | None = None

    def __new__(cls, *, echo: bool = False) -> DatabaseService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *, echo: bool = False):
        if hasattr(self, "_engine"):  # Already initialized
            return

        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._echo = echo

    def get_database_url(self) -> str:
        """Get the current database URL from configuration."""
        return get_database_url()

    # =====================================================================
    # Connection & Session Management
    # =====================================================================

    def is_connected(self) -> bool:
        """Return True if the engine/metadata are initialised."""
        return self._engine is not None

    def is_registered(self) -> bool:
        """Return True if models are registered with the database."""
        return self.is_connected()

    async def connect(self, database_url: str | None = None, *, echo: bool | None = None) -> None:
        """Initialize the async engine and create all tables."""
        if self.is_connected():
            logger.warning("Database engine already connected - reusing existing engine")
            return

        database_url = database_url or get_database_url()
        if not database_url:
            error_msg = "DATABASE_URL environment variable must be set before connecting to the DB"
            raise RuntimeError(error_msg)

        # Convert sync URLs to async
        if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        echo_setting = echo if echo is not None else self._echo

        logger.debug(f"Creating async SQLAlchemy engine (echo={echo_setting})")

        # Enhanced connection configuration based on SQLModel best practices
        connect_args = {}
        if "sqlite" in database_url:
            # SQLite-specific optimizations
            connect_args = {
                "check_same_thread": False,
                "timeout": 30,
            }
        elif "postgresql" in database_url:
            # PostgreSQL-specific optimizations
            connect_args = {
                "server_settings": {
                    "timezone": "UTC",
                    "application_name": "TuxBot",
                },
            }

        self._engine = create_async_engine(
            database_url,
            echo=echo_setting,
            future=True,
            pool_pre_ping=True,
            pool_size=15,
            max_overflow=30,
            pool_timeout=60,
            pool_recycle=3600,
            pool_reset_on_return="rollback",
            connect_args=connect_args
            | (
                {
                    "command_timeout": 60,
                    "server_settings": {
                        **(connect_args.get("server_settings") or {}),  # pyright: ignore[reportGeneralTypeIssues]
                        "statement_timeout": "60s",
                        "idle_in_transaction_session_timeout": "300s",
                        "lock_timeout": "30s",
                        "tcp_keepalives_idle": "600",
                        "tcp_keepalives_interval": "30",
                        "tcp_keepalives_count": "3",
                    },
                }
                if "postgresql" in database_url
                else {}
            ),
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Successfully connected to database via SQLAlchemy")

    async def create_tables(self) -> None:
        """Create all tables in the database."""
        if not self.is_connected():
            await self.connect()

        assert self._engine is not None
        async with self._engine.begin() as conn:
            # Use checkfirst=True to avoid errors if tables already exist
            await conn.run_sync(lambda sync_conn: SQLModel.metadata.create_all(sync_conn, checkfirst=True))
        logger.info("Created all database tables")

    async def disconnect(self) -> None:
        """Dispose the engine and tear-down the connection pool."""
        if not self.is_connected():
            logger.warning("Database engine not connected - nothing to disconnect")
            return

        assert self._engine is not None
        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("Disconnected from database")

    async def health_check(self) -> dict[str, Any]:
        """Perform a database health check."""
        if not self.is_connected():
            return {"status": "disconnected", "error": "Database engine not connected"}

        try:
            async with self.session() as session:
                # Simple query to test connectivity
                from sqlalchemy import text  # noqa: PLC0415

                result = await session.execute(text("SELECT 1"))
                value = result.scalar()

                if value == 1:
                    return {
                        "status": "healthy",
                        "pool_size": getattr(self._engine.pool, "size", "unknown") if self._engine else "unknown",
                        "checked_connections": getattr(self._engine.pool, "checkedin", "unknown")
                        if self._engine
                        else "unknown",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                return {"status": "unhealthy", "error": "Unexpected query result"}

        except Exception as exc:
            logger.error(f"Database health check failed: {exc}")
            return {"status": "unhealthy", "error": str(exc)}

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Return an async SQLAlchemy session context-manager."""
        if not self.is_connected():
            await self.connect()
            if not self.is_connected():
                error_msg = "Database engine not initialised - call connect() first"
                raise RuntimeError(error_msg)

        assert self._session_factory is not None
        async with self._session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession]:
        """Synonym for session() - kept for API compatibility."""
        async with self.session() as sess:
            yield sess

    # =====================================================================
    # Controller Access - Lazy Loading Pattern
    # =====================================================================

    @property
    def guild(self):
        """Get the guild controller."""
        if not hasattr(self, "_guild_controller"):
            from tux.database.controllers.guild import GuildController  # noqa: PLC0415

            self._guild_controller = GuildController(self)
        return self._guild_controller

    @property
    def guild_config(self):
        """Get the guild config controller."""
        if not hasattr(self, "_guild_config_controller"):
            from tux.database.controllers.guild_config import GuildConfigController  # noqa: PLC0415

            self._guild_config_controller = GuildConfigController(self)
        return self._guild_config_controller

    @property
    def afk(self):
        """Get the AFK controller."""
        if not hasattr(self, "_afk_controller"):
            from tux.database.controllers.afk import AfkController  # noqa: PLC0415

            self._afk_controller = AfkController(self)
        return self._afk_controller

    @property
    def levels(self):
        """Get the levels controller."""
        if not hasattr(self, "_levels_controller"):
            from tux.database.controllers.levels import LevelsController  # noqa: PLC0415

            self._levels_controller = LevelsController(self)
        return self._levels_controller

    @property
    def snippet(self):
        """Get the snippet controller."""
        if not hasattr(self, "_snippet_controller"):
            from tux.database.controllers.snippet import SnippetController  # noqa: PLC0415

            self._snippet_controller = SnippetController(self)
        return self._snippet_controller

    @property
    def case(self):
        """Get the case controller."""
        if not hasattr(self, "_case_controller"):
            from tux.database.controllers.case import CaseController  # noqa: PLC0415

            self._case_controller = CaseController(self)
        return self._case_controller

    @property
    def starboard(self):
        """Get the starboard controller."""
        if not hasattr(self, "_starboard_controller"):
            from tux.database.controllers.starboard import StarboardController  # noqa: PLC0415

            self._starboard_controller = StarboardController(self)
        return self._starboard_controller

    @property
    def starboard_message(self):
        """Get the starboard message controller."""
        if not hasattr(self, "_starboard_message_controller"):
            from tux.database.controllers.starboard import StarboardMessageController  # noqa: PLC0415

            self._starboard_message_controller = StarboardMessageController(self)
        return self._starboard_message_controller

    @property
    def reminder(self):
        """Get the reminder controller."""
        if not hasattr(self, "_reminder_controller"):
            from tux.database.controllers.reminder import ReminderController  # noqa: PLC0415

            self._reminder_controller = ReminderController(self)
        return self._reminder_controller

    # =====================================================================
    # Enhanced Utility Methods - Based on py-pglite Patterns
    # =====================================================================

    async def execute_with_retry(
        self,
        operation: Callable[[AsyncSession], Awaitable[T]],
        span_desc: str,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> T:
        """
        Execute operation with exponential backoff retry logic.

        Based on py-pglite reliability patterns for handling connection issues.
        """
        for attempt in range(max_retries):
            try:
                if sentry_sdk.is_initialized():
                    with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                        span.set_tag("db.service", "DatabaseService")
                        span.set_tag("attempt", attempt + 1)
                        try:
                            async with self.session() as session:
                                result = await operation(session)
                        except Exception as exc:
                            span.set_status("internal_error")
                            span.set_data("error", str(exc))
                            raise
                        else:
                            span.set_status("ok")
                            return result
                else:
                    async with self.session() as session:
                        return await operation(session)

            except (sqlalchemy.exc.DisconnectionError, TimeoutError, sqlalchemy.exc.OperationalError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                    raise

                wait_time = backoff_factor * (2**attempt)
                logger.warning(f"Database operation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"{span_desc}: {e}")
                raise

        # This should never be reached, but satisfies the type checker
        error_msg = f"Unexpected exit from retry loop in {span_desc}"
        raise RuntimeError(error_msg)

    async def execute_query(self, operation: Callable[[AsyncSession], Awaitable[T]], span_desc: str) -> T:
        """Run operation inside a managed session & sentry span (with retry logic)."""
        return await self.execute_with_retry(operation, span_desc)

    async def execute_transaction(self, callback: Callable[[], Awaitable[T]]) -> T:
        """Execute callback inside a database session / transaction block."""
        try:
            async with self.transaction():
                return await callback()
        except Exception as exc:
            logger.error(f"Transaction failed: {exc}")
            raise

    async def get_database_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive database metrics for monitoring.

        Based on py-pglite monitoring patterns.
        """

        async def _get_metrics(session: AsyncSession) -> dict[str, Any]:
            # Connection pool metrics
            pool_metrics = {
                "pool_size": getattr(self._engine.pool, "size", "unknown") if self._engine else "unknown",
                "checked_in": getattr(self._engine.pool, "checkedin", "unknown") if self._engine else "unknown",
                "checked_out": getattr(self._engine.pool, "checkedout", "unknown") if self._engine else "unknown",
                "overflow": getattr(self._engine.pool, "overflow", "unknown") if self._engine else "unknown",
            }

            # Table statistics
            table_stats = await session.execute(
                text("""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    seq_scan,
                    idx_scan
                FROM pg_stat_user_tables
                ORDER BY tablename
            """),
            )

            # Database-wide statistics
            db_stats = await session.execute(
                text("""
                SELECT
                    numbackends as active_connections,
                    xact_commit as committed_transactions,
                    xact_rollback as rolled_back_transactions,
                    blks_read as blocks_read,
                    blks_hit as blocks_hit,
                    tup_returned as tuples_returned,
                    tup_fetched as tuples_fetched,
                    tup_inserted as tuples_inserted,
                    tup_updated as tuples_updated,
                    tup_deleted as tuples_deleted
                FROM pg_stat_database
                WHERE datname = current_database()
            """),
            )

            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "pool": pool_metrics,
                "tables": [dict(row._mapping) for row in table_stats.fetchall()],  # pyright: ignore[reportPrivateUsage]
                "database": dict(db_row._mapping) if (db_row := db_stats.fetchone()) else {},  # pyright: ignore[reportPrivateUsage]
            }

        return await self.execute_query(_get_metrics, "get_database_metrics")

    async def analyze_query_performance(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Analyze query performance with EXPLAIN ANALYZE.

        Development utility based on py-pglite query optimization patterns.
        """

        async def _analyze(session: AsyncSession) -> dict[str, Any]:
            # Get execution plan
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = await session.execute(text(explain_query), params or {})
            plan_data = result.scalar()

            return {
                "query": query,
                "params": params,
                "plan": plan_data[0] if plan_data else {},
                "analyzed_at": datetime.now(UTC).isoformat(),
            }

        return await self.execute_query(_analyze, "analyze_query_performance")

    async def run_migrations(self) -> bool:
        """
        Run pending Alembic migrations programmatically.

        Based on py-pglite deployment patterns.
        """
        try:
            from alembic import command  # noqa: PLC0415
            from alembic.config import Config  # noqa: PLC0415

            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.get_database_url())

            logger.info("Running database migrations...")
            command.upgrade(alembic_cfg, "head")
        except ImportError:
            logger.warning("Alembic not available - skipping migrations")
            return False
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        else:
            logger.info("Database migrations completed successfully")
            return True

    async def reset_database_stats(self) -> bool:
        """Reset PostgreSQL statistics for clean monitoring."""

        async def _reset_stats(session: AsyncSession) -> bool:
            await session.execute(text("SELECT pg_stat_reset();"))
            return True

        try:
            return await self.execute_query(_reset_stats, "reset_database_stats")
        except Exception as e:
            logger.error(f"Failed to reset database stats: {e}")
            return False

    async def reset_database_for_tests(self, preserve_schema: bool = True) -> bool:
        """
        Comprehensive database reset for integration tests.

        Args:
            preserve_schema: If True, keeps table structure and only clears data.
                           If False, drops all tables and recreates schema.

        Returns:
            bool: True if reset was successful, False otherwise.

        Based on py-pglite reset patterns for safe test isolation.
        """
        try:
            if preserve_schema:
                return await self._reset_data_only()
            return await self._reset_full_schema()
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return False

    async def _reset_data_only(self) -> bool:
        """Reset data while preserving schema (faster for most tests)."""

        async def _truncate_all_data(session: AsyncSession) -> bool:
            # Get all table names (excluding system tables and alembic)
            result = await session.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name NOT IN ('alembic_version', 'spatial_ref_sys')
                ORDER BY table_name
            """),
            )

            table_names = [row[0] for row in result.fetchall()]

            if not table_names:
                logger.info("No tables found to truncate")
                return True

            # Disable foreign key constraints temporarily
            await session.execute(text("SET session_replication_role = replica;"))

            try:
                # Truncate all tables with CASCADE and restart sequences
                for table_name in table_names:
                    try:
                        await session.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;'))
                        logger.debug(f"Truncated table: {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not truncate table {table_name}: {e}")

                # Reset sequences to ensure predictable IDs
                sequences_result = await session.execute(
                    text("""
                    SELECT sequence_name
                    FROM information_schema.sequences
                    WHERE sequence_schema = 'public'
                """),
                )

                sequences = [row[0] for row in sequences_result.fetchall()]
                for seq_name in sequences:
                    try:
                        await session.execute(text(f"SELECT setval('{seq_name}', 1, false)"))
                    except Exception as e:
                        logger.warning(f"Could not reset sequence {seq_name}: {e}")

                await session.commit()
                logger.info(f"Successfully truncated {len(table_names)} tables")
                return True

            finally:
                # Re-enable foreign key constraints
                await session.execute(text("SET session_replication_role = DEFAULT;"))

        return await self.execute_with_retry(_truncate_all_data, "reset_data_only")

    async def _reset_full_schema(self) -> bool:
        """Complete schema reset (drops and recreates all tables)."""

        async def _drop_and_recreate_schema(session: AsyncSession) -> bool:
            # Drop all tables, views, and sequences (one command at a time for asyncpg)
            await session.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
            await session.execute(text("CREATE SCHEMA public;"))
            await session.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            await session.execute(text("GRANT ALL ON SCHEMA public TO current_user;"))

            await session.commit()
            logger.info("Dropped and recreated public schema")
            return True

        success = await self.execute_with_retry(_drop_and_recreate_schema, "reset_full_schema")

        if success:
            # Recreate tables using SQLModel metadata
            try:
                if not self._engine:
                    msg = "Database engine not initialized"
                    raise RuntimeError(msg)  # noqa: TRY301
                async with self._engine.begin() as conn:
                    await conn.run_sync(
                        lambda sync_conn: SQLModel.metadata.create_all(sync_conn, checkfirst=False),
                    )
            except Exception as e:
                logger.error(f"Failed to recreate schema: {e}")
                return False
            else:
                logger.info("Successfully recreated database schema")
                return True

        return False

    async def setup_test_database(self, run_migrations: bool = False) -> bool:
        """
        Complete test database setup with optional migrations.

        Args:
            run_migrations: Whether to run Alembic migrations after schema creation

        Returns:
            bool: True if setup was successful
        """
        try:
            # Reset database
            if not await self.reset_database_for_tests(preserve_schema=False):
                logger.error("Failed to reset database")
                return False

            # Run migrations if requested
            if run_migrations:
                if not await self.run_migrations():
                    logger.error("Failed to run migrations")
                    return False
                logger.info("Database migrations completed")
            else:
                # Create tables directly from SQLModel metadata
                await self.create_tables()
                logger.info("Database tables created from SQLModel metadata")

            # Verify setup
            health = await self.health_check()
            if health["status"] != "healthy":
                logger.error(f"Database health check failed: {health}")
                return False

        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
        else:
            logger.info("Test database setup completed successfully")
            return True

    async def get_table_row_counts(self) -> dict[str, int]:
        """Get row counts for all tables (useful for test verification)."""

        async def _get_counts(session: AsyncSession) -> dict[str, int]:  # pyright: ignore[reportUnknownVariableType]
            result = await session.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name != 'alembic_version'
                ORDER BY table_name
            """),
            )

            table_names = [row[0] for row in result.fetchall()]
            counts = {}

            for table_name in table_names:
                count_result = await session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                counts[table_name] = count_result.scalar()

            return counts  # pyright: ignore[reportUnknownVariableType]

        try:
            return await self.execute_query(_get_counts, "get_table_row_counts")
        except Exception as e:
            logger.error(f"Failed to get table row counts: {e}")
            return {}

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the async engine for testing purposes."""
        return self._engine

    # Legacy compatibility
    @property
    def manager(self) -> DatabaseService:
        """Legacy compatibility - return self as manager."""
        return self
