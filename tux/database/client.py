from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel


class DatabaseClient:
    """Singleton wrapper around an *async* SQLAlchemy engine / session factory.

    This class provides a clean async interface for database operations using SQLModel
    and SQLAlchemy. All interactions go through an :pyclass:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    _instance: DatabaseClient | None = None

    def __new__(cls) -> DatabaseClient:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    def is_connected(self) -> bool:
        """Return True if the engine/metadata are initialised."""
        return self._engine is not None

    # Existing code queried `db.is_registered()` to check models; same semantics
    def is_registered(self) -> bool:
        return self.is_connected()

    async def connect(self, database_url: str | None = None, *, echo: bool = False) -> None:
        """Initialise the async engine and create all tables.

        The *first* call performs initialisation - every subsequent call is a
        no-op (but will log a warning).
        """
        if self.is_connected():
            logger.warning("Database engine already connected - reusing existing engine")
            return

        database_url = database_url or os.getenv("DATABASE_URL")
        if not database_url:
            error_msg = "DATABASE_URL environment variable must be set before connecting to the DB"
            raise RuntimeError(error_msg)

        # SQLAlchemy async engines expect an async driver (e.g. asyncpg for Postgres)
        # If the user provided a sync URL, we attempt to coerce it to async-pg URL.
        if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        logger.debug(f"Creating async SQLAlchemy engine (echo={echo})")
        self._engine = create_async_engine(database_url, echo=echo, future=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

        # Create tables (auto-create helps during development & tests, migrations
        # are handled by Alembic).
        async with self._engine.begin() as conn:  # type: ignore[attr-defined]
            await conn.run_sync(SQLModel.metadata.create_all)  # type: ignore[attr-defined]

        logger.info("Successfully connected to database via SQLModel/SQLAlchemy")

    async def disconnect(self) -> None:
        """Dispose the engine and tear-down the connection pool."""
        if not self.is_connected():
            logger.warning("Database engine not connected - nothing to disconnect")
            return

        assert self._engine is not None  # mypy
        await self._engine.dispose()  # type: ignore[attr-defined]
        self._engine = None
        self._session_factory = None
        logger.info("Disconnected from database")

    # ------------------------------------------------------------------
    # Session / transaction helpers
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Return an async SQLAlchemy session context-manager."""
        if not self.is_connected():
            error_msg = "Database engine not initialised - call connect() first"
            raise RuntimeError(error_msg)
        assert self._session_factory is not None  # mypy
        async with self._session_factory() as sess:  # type: ignore[attr-defined]
            try:
                yield sess
                await sess.commit()  # type: ignore[attr-defined]
            except Exception:
                await sess.rollback()  # type: ignore[attr-defined]
                raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession]:
        """Synonym for :pyfunc:`session` - kept for API parity."""
        async with self.session() as sess:
            yield sess


# A *process-level* singleton instance - mirrors the old behaviour
# where the database client lives at ``tux.database.client.db``.

db = DatabaseClient()
