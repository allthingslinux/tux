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
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

import sentry_sdk
import sqlalchemy.exc
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

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

            logger.info("✅ Successfully connected to database")

        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {type(e).__name__}")
            logger.info("💡 Check your database connection settings and ensure PostgreSQL is running")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the database and dispose of the connection pool."""
        if self._engine:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("✅ Disconnected from database")

    def is_connected(self) -> bool:
        """Check if database is currently connected.

        Returns
        -------
        bool
            True if connected, False otherwise.
        """
        return self._engine is not None

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

    async def execute_query(self, operation: Callable[[AsyncSession], Awaitable[T]], span_desc: str) -> T:
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
        for attempt in range(max_retries):
            try:
                if sentry_sdk.is_initialized():
                    with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                        span.set_tag("db.service", "DatabaseService")
                        span.set_tag("attempt", attempt + 1)

                        async with self.session() as sess:
                            result = await operation(sess)

                            span.set_status("ok")
                            return result
                else:
                    async with self.session() as sess:
                        return await operation(sess)

            except (sqlalchemy.exc.DisconnectionError, TimeoutError, sqlalchemy.exc.OperationalError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"❌ Database operation failed after {max_retries} attempts: {type(e).__name__}")
                    logger.info("💡 Check your database connection and consider restarting PostgreSQL")
                    raise

                wait_time = backoff_factor * (2**attempt)
                logger.warning(f"⚠️  Database operation failed (attempt {attempt + 1}), retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"❌ {span_desc}: {type(e).__name__}")
                logger.info("💡 Check your database configuration and network connection")
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
                return {"status": "unhealthy", "error": "Unexpected health check result"}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
