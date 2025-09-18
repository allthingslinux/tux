"""
Clean Async-Agnostic Database Service Architecture

This module provides a clean, maintainable database service that supports
both async and sync operations through proper architectural separation.

Architecture:
- DatabaseServiceABC: Abstract base class defining the interface
- AsyncDatabaseService: Async implementation for production PostgreSQL
- SyncDatabaseService: Sync implementation for testing/unit tests
- DatabaseServiceFactory: Factory to create appropriate service

Key Principles:
- Clean separation between sync and async modes
- Dependency injection for session factories
- No complex conditional logic or hacks
- Type-safe interfaces
- Easy to test and maintain
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Protocol, TypeVar

import sentry_sdk
import sqlalchemy.exc
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

from tux.shared.config import CONFIG

T = TypeVar("T")


class DatabaseMode(Enum):
    """Supported database operation modes."""

    ASYNC = "async"
    SYNC = "sync"


class SessionFactory(Protocol):
    """Protocol for session factories."""

    def __call__(self) -> AsyncSession | Session: ...


class DatabaseServiceABC(ABC):
    """Abstract base class for all database services."""

    @abstractmethod
    async def connect(self, database_url: str, **kwargs: Any) -> None:
        """Connect to database."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from database."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected."""

    @abstractmethod
    async def session(self) -> Any:
        """Get database session context manager."""

    @abstractmethod
    async def execute_query(self, operation: Callable[[Any], Awaitable[T]], span_desc: str) -> T:
        """Execute database operation with retry logic."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform database health check."""


class AsyncDatabaseService(DatabaseServiceABC):
    """Async database service implementation."""

    def __init__(self, echo: bool = False):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._echo = echo

    async def connect(self, database_url: str, **kwargs: Any) -> None:
        """Connect to async database."""
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

            logger.info("✅ Successfully connected to async database")

        except Exception as e:
            logger.error(f"❌ Failed to connect to async database: {type(e).__name__}")
            logger.info("💡 Check your database connection settings and ensure PostgreSQL is running")
            logger.info("   You can start it with: make docker-up")
            raise

    async def disconnect(self) -> None:
        """Disconnect from async database."""
        if self._engine:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("✅ Disconnected from async database")

    def is_connected(self) -> bool:
        """Check if async database is connected."""
        return self._engine is not None

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the async database engine (for testing purposes)."""
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:  # type: ignore
        """Get async database session."""
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
        """Execute callback inside a transaction."""
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
        """Execute async database operation with retry logic."""
        return await self._execute_with_retry(operation, span_desc)

    async def _execute_with_retry(
        self,
        operation: Callable[[AsyncSession], Awaitable[T]],
        span_desc: str,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> T:
        """Internal retry logic for async operations."""
        for attempt in range(max_retries):
            try:
                if sentry_sdk.is_initialized():
                    with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                        span.set_tag("db.service", "AsyncDatabaseService")
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
        """Perform async database health check."""
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


class SyncDatabaseService(DatabaseServiceABC):
    """Sync database service implementation."""

    def __init__(self, echo: bool = False):
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._echo = echo

    async def connect(self, database_url: str, **kwargs: Any) -> None:
        """Connect to sync database."""
        try:
            self._engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600, echo=self._echo, **kwargs)

            self._session_factory = sessionmaker(
                self._engine,
                class_=Session,
                expire_on_commit=False,
            )

            logger.info("Successfully connected to sync database")

        except Exception as e:
            logger.error(f"Failed to connect to sync database: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from sync database."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Disconnected from sync database")

    def is_connected(self) -> bool:
        """Check if sync database is connected."""
        return self._engine is not None

    @property
    def engine(self) -> Engine | None:
        """Get the sync database engine (for testing purposes)."""
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[Session]:  # type: ignore
        """Get sync database session wrapped in async context."""
        if not self.is_connected() or not self._session_factory:
            # For sync databases in tests, we'll use a simple in-memory setup
            await self.connect("sqlite:///:memory:")

        assert self._session_factory is not None

        # Use asyncio.to_thread to run sync operations in a thread
        session = await asyncio.to_thread(self._session_factory)

        try:
            yield session
            await asyncio.to_thread(session.commit)
        except Exception:
            await asyncio.to_thread(session.rollback)
            raise
        finally:
            await asyncio.to_thread(session.close)

    async def execute_query(self, operation: Callable[[Session], T], span_desc: str) -> T:
        """Execute sync database operation with retry logic."""
        return await self._execute_with_retry(operation, span_desc)

    async def _execute_with_retry(
        self,
        operation: Callable[[Session], T],
        span_desc: str,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> T:
        """Internal retry logic for sync operations."""
        for attempt in range(max_retries):
            try:
                if sentry_sdk.is_initialized():
                    with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                        span.set_tag("db.service", "SyncDatabaseService")
                        span.set_tag("attempt", attempt + 1)

                        async with self.session() as sess:
                            result = await asyncio.to_thread(operation, sess)

                        span.set_status("ok")
                        return result
                else:
                    async with self.session() as sess:
                        return await asyncio.to_thread(operation, sess)

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
        """Perform sync database health check."""
        if not self.is_connected():
            return {"status": "disconnected", "error": "Database engine not connected"}

        try:
            async with self.session() as session:
                result = await asyncio.to_thread(session.execute, text("SELECT 1 as health_check"))
                value = result.scalar()

                if value == 1:
                    return {"status": "healthy", "mode": "sync"}
                return {"status": "unhealthy", "error": "Unexpected health check result"}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class DatabaseServiceFactory:
    """Factory to create appropriate database service."""

    @staticmethod
    def create(mode: DatabaseMode, echo: bool = False) -> DatabaseServiceABC:
        """Create database service based on mode."""
        if mode == DatabaseMode.ASYNC:
            return AsyncDatabaseService(echo=echo)
        if mode == DatabaseMode.SYNC:
            return SyncDatabaseService(echo=echo)
        msg = f"Unsupported database mode: {mode}"
        raise ValueError(msg)

    @staticmethod
    def create_from_url(database_url: str, echo: bool = False) -> DatabaseServiceABC:
        """Create database service based on URL."""
        if "+psycopg_async://" in database_url or "postgresql" in database_url:
            return AsyncDatabaseService(echo=echo)
        # Assume sync for SQLite and other databases
        return SyncDatabaseService(echo=echo)


# Legacy alias for backward compatibility during transition
DatabaseService = AsyncDatabaseService


# Clean test utilities
def create_test_database_service(mode: DatabaseMode = DatabaseMode.SYNC, echo: bool = False) -> DatabaseServiceABC:
    """Create database service for testing."""
    return DatabaseServiceFactory.create(mode, echo=echo)


async def setup_test_database(service: DatabaseServiceABC, database_url: str) -> None:
    """Setup test database."""
    await service.connect(database_url)

    # Create tables if needed
    if isinstance(service, SyncDatabaseService) and service.engine:
        # For sync service, create tables directly
        SQLModel.metadata.create_all(service.engine, checkfirst=False)

    logger.info("Test database setup complete")


async def teardown_test_database(service: DatabaseServiceABC) -> None:
    """Teardown test database."""
    await service.disconnect()
    logger.info("Test database torn down")
