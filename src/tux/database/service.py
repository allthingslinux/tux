"""
Database Service for Tux Bot.

This module provides a clean, maintainable database service for async PostgreSQL operations.

Key Principles:
- Async-first design
- Connection pooling with retry logic
- Type-safe interfaces
- Automatic reconnection handling
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

import sentry_sdk
import sqlalchemy.exc
from loguru import logger
from sqlalchemy import inspect, text
from sqlalchemy.engine.interfaces import ReflectedColumn
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from tux.services.sentry.metrics import record_database_metric
from tux.shared.config import CONFIG

T = TypeVar("T")

__all__ = ["DatabaseService"]


class DatabaseService:
    """
    Async database service for PostgreSQL.

    Provides connection management, session handling, query execution with retry logic,
    and health checks for the PostgreSQL database.

    Attributes
    ----------
    _engine : AsyncEngine | None
        SQLAlchemy async engine for database connections.
    _session_factory : async_sessionmaker[AsyncSession] | None
        Factory for creating database sessions.
    _echo : bool
        Whether to log SQL queries (useful for debugging).
    """

    def __init__(self, echo: bool = False):
        """Initialize the database service.

        Parameters
        ----------
        echo : bool, optional
            Whether to enable SQL query logging (default is False).
        """
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._echo = echo

    async def connect(self, database_url: str, **kwargs: Any) -> None:
        """
        Connect to the PostgreSQL database.

        Parameters
        ----------
        database_url : str
            PostgreSQL connection URL in format:
            postgresql+psycopg://user:password@host:port/database
        **kwargs : Any
            Additional arguments passed to create_async_engine.
        """
        try:
            self._engine = create_async_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self._echo,
                **kwargs,
            )

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.success("Successfully connected to database")

        except Exception as e:
            logger.error(f"Failed to connect to database: {type(e).__name__}")
            logger.info(
                "Check your database connection settings and ensure PostgreSQL is running",
            )
            raise

    async def disconnect(self) -> None:
        """Disconnect from the database and dispose of the connection pool."""
        if self._engine:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("Disconnected from database")

    def is_connected(self) -> bool:
        """Check if database is currently connected.

        Returns
        -------
        bool
            True if connected, False otherwise.
        """
        return self._engine is not None

    async def test_connection(self) -> None:
        """Test database connectivity with a simple query.

        Raises
        ------
        Exception
            If the database connection fails or the test query fails.
        """
        if not self._engine:
            msg = "Database engine not initialized"
            raise RuntimeError(msg)

        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Database connectivity test failed: {e}", exc_info=True)
            # Capture exception with database context for Sentry
            # Note: self._engine is guaranteed to be not None here due to check above
            # Lazy import to avoid circular dependency: tux.database.service → tux.services.sentry → tux.core.context → tux.database.controllers → tux.database.service
            from tux.services.sentry import capture_database_error  # noqa: PLC0415

            with sentry_sdk.push_scope() as scope:
                # Use tag for filtering (operation type)
                scope.set_tag("database.operation", "test_connection")

                capture_database_error(
                    e,
                    operation="test_connection",
                )
            raise

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the database engine.

        Returns
        -------
        AsyncEngine | None
            The SQLAlchemy async engine, or None if not connected.

        Notes
        -----
        Primarily used for testing and advanced operations.
        """
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Get a database session context manager.

        Automatically handles connection, commit, and rollback.

        Yields
        ------
        AsyncSession
            An active database session.

        Examples
        --------
        >>> async with db.session() as session:
        ...     result = await session.execute(select(User))
        ...     users = result.scalars().all()
        """
        if not self.is_connected() or not self._session_factory:
            await self.connect(CONFIG.database_url)

        assert self._session_factory is not None

        async with self._session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """
        Execute a callback inside a database transaction.

        Parameters
        ----------
        callback : Callable[[], Any]
            Async function to execute within the transaction.

        Returns
        -------
        Any
            The return value of the callback function.

        Notes
        -----
        If the transaction fails, it will be rolled back automatically.
        """
        if not self.is_connected() or not self._session_factory:
            await self.connect(CONFIG.database_url)

        assert self._session_factory is not None

        async with self._session_factory() as sess, sess.begin():
            try:
                return await callback()
            except Exception:
                await sess.rollback()
                raise

    async def execute_query(
        self,
        operation: Callable[[AsyncSession], Awaitable[T]],
        span_desc: str,
    ) -> T:
        """
        Execute database operation with automatic retry logic.

        Parameters
        ----------
        operation : Callable[[AsyncSession], Awaitable[T]]
            Async function that performs database operations.
        span_desc : str
            Description for Sentry performance monitoring.

        Returns
        -------
        T
            Result of the operation.

        Notes
        -----
        Retries the operation automatically on transient failures.
        """
        return await self._execute_with_retry(operation, span_desc)

    async def _execute_with_retry(
        self,
        operation: Callable[[AsyncSession], Awaitable[T]],
        span_desc: str,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> T:
        """
        Execute database operation with exponential backoff retry logic.

        Parameters
        ----------
        operation : Callable[[AsyncSession], Awaitable[T]]
            Database operation to execute.
        span_desc : str
            Description for monitoring/logging.
        max_retries : int, optional
            Maximum number of retry attempts (default is 3).
        backoff_factor : float, optional
            Multiplier for exponential backoff (default is 0.5).

        Returns
        -------
        T
            Result of the operation.

        Raises
        ------
        TimeoutError
            If the operation times out after all retries.
        sqlalchemy.exc.DisconnectionError
            If database disconnection occurs after all retries.
        sqlalchemy.exc.OperationalError
            If database operational error occurs after all retries.
        RuntimeError
            If the retry loop completes unexpectedly without return or exception.
        """
        start_time = time.perf_counter()
        retry_count = 0
        operation_name = span_desc.split(":")[0] if ":" in span_desc else "query"

        for attempt in range(max_retries):
            try:
                if sentry_sdk.is_initialized():
                    with sentry_sdk.start_span(
                        op="db.query",
                        name=span_desc,
                    ) as span:
                        # Use set_data() for span attributes (context in trace view)
                        span.set_data("db.service", "DatabaseService")
                        span.set_data("db.operation", operation_name)
                        span.set_data("db.attempt", attempt + 1)
                        span.set_data("db.retry_count", retry_count)

                        async with self.session() as sess:
                            result = await operation(sess)

                            duration_ms = (time.perf_counter() - start_time) * 1000
                            span.set_data("db.duration_ms", duration_ms)
                            span.set_status("ok")

                            # Record metrics for aggregation (separate from span data)
                            record_database_metric(
                                operation=operation_name,
                                duration_ms=duration_ms,
                                retry_count=retry_count,
                                success=True,
                            )

                            return result
                else:
                    async with self.session() as sess:
                        return await operation(sess)

            except (
                sqlalchemy.exc.DisconnectionError,
                TimeoutError,
                sqlalchemy.exc.OperationalError,
            ) as e:
                retry_count += 1
                if attempt == max_retries - 1:
                    logger.error(
                        f"Database operation failed after {max_retries} attempts: {type(e).__name__}",
                    )
                    logger.info(
                        "Check your database connection and consider restarting PostgreSQL",
                    )

                    # Record failed database metric
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    record_database_metric(
                        operation=operation_name,
                        duration_ms=duration_ms,
                        retry_count=retry_count,
                        success=False,
                        error_type=type(e).__name__,
                    )

                    raise

                wait_time = backoff_factor * (2**attempt)
                logger.warning(
                    f"Database operation failed (attempt {attempt + 1}), retrying in {wait_time}s",
                )
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"{span_desc}: {type(e).__name__}")
                logger.info("Check your database configuration and network connection")

                # Record failed database metric
                duration_ms = (time.perf_counter() - start_time) * 1000

                record_database_metric(
                    operation=operation_name,
                    duration_ms=duration_ms,
                    retry_count=retry_count,
                    success=False,
                    error_type=type(e).__name__,
                )

                raise

        # This should never be reached
        msg = f"Unexpected exit from retry loop in {span_desc}"
        raise RuntimeError(msg)

    async def health_check(self) -> dict[str, Any]:
        """Perform database health check.

        Returns
        -------
        dict[str, Any]
            Health check result with status and optional error message.
            Status can be: "healthy", "unhealthy", or "disconnected".

        Examples
        --------
        >>> result = await db.health_check()
        >>> print(result)
        {'status': 'healthy', 'mode': 'async'}
        """
        if not self.is_connected():
            return {"status": "disconnected", "error": "Database engine not connected"}

        try:
            async with self.session() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                value = result.scalar()

                if value == 1:
                    return {"status": "healthy", "mode": "async"}
                return {
                    "status": "unhealthy",
                    "error": "Unexpected health check result",
                }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def validate_schema(self) -> dict[str, Any]:
        """
        Validate that the database schema matches the current model definitions.

        Uses SQLAlchemy's metadata reflection to compare the actual database schema
        with the defined model metadata. Much more efficient and accurate than
        manual queries.

        Returns
        -------
        dict[str, Any]
            Schema validation result with status and optional error message.
            Status can be: "valid", "invalid", or "error".

        Examples
        --------
        >>> result = await db.validate_schema()
        >>> print(result)
        {'status': 'valid', 'mode': 'async'}
        """
        if not self.is_connected():
            return {"status": "error", "error": "Database engine not connected"}

        try:
            # Get database inspector to reflect current schema
            # Type checker doesn't know engine is not None after is_connected() check
            assert self._engine is not None, (
                "Engine should not be None after connection check"
            )
            async with self._engine.begin() as conn:
                inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))

                # Check if required tables exist
                existing_tables = await conn.run_sync(
                    lambda sync_conn: inspector.get_table_names(),
                )
                # Get table names from SQLModel metadata (models with table=True)
                required_tables = set(SQLModel.metadata.tables.keys())

                if missing_tables := required_tables - set(existing_tables):
                    return {
                        "status": "invalid",
                        "error": f"Missing tables: {', '.join(missing_tables)}. Run 'uv run db reset' to fix.",
                    }

                # Helper function to get columns for a table
                def get_table_columns(
                    sync_conn: Any,
                    table_name: str,
                ) -> list[ReflectedColumn]:
                    return inspector.get_columns(table_name)

                # Check that all model columns exist in database (1-to-1 validation)
                missing_columns: list[str] = []
                for table_name in required_tables:
                    # Get columns from database
                    columns = await conn.run_sync(get_table_columns, table_name)
                    db_column_names = {col["name"] for col in columns}

                    # Get columns from model metadata
                    if table_name in SQLModel.metadata.tables:
                        table_metadata = SQLModel.metadata.tables[table_name]
                        model_column_names = {
                            col.name for col in table_metadata.columns
                        }

                        # Find missing columns
                        missing_for_table = model_column_names - db_column_names
                        if missing_for_table:
                            missing_columns.extend(
                                [f"{table_name}.{col}" for col in missing_for_table],
                            )

                if missing_columns:
                    return {
                        "status": "invalid",
                        "error": f"Missing columns: {', '.join(missing_columns)}. Run 'uv run db reset' to fix.",
                    }

                return {"status": "valid", "mode": "async"}

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error(f"Database schema validation failed: {error_msg}")
            logger.error(
                "This usually means the database schema doesn't match the model definitions",
            )
            logger.error("Try running: uv run db reset")
            return {"status": "invalid", "error": error_msg}
