from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel


class DatabaseClient:
    """Singleton wrapper around an *async* SQLAlchemy engine / session factory.

    This class replaces the previous Prisma-based client while exposing a very
    similar public API so that the higher-level controllers require only minimal
    changes.  All interactions go through an :pyclass:`~sqlalchemy.ext.asyncio.AsyncSession`.
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

    @property
    def is_connected(self) -> bool:  # noqa: D401 – property
        """Return True if the engine/metadata are initialised."""
        return self._engine is not None

    # Back-compat: expose old callable form
    def is_connected_call(self) -> bool:  # noqa: D401
        return self.is_connected

    # Existing code queried `db.is_registered()` to check models; same semantics
    def is_registered(self) -> bool:  # noqa: D401
        return self.is_connected


    async def connect(self, database_url: str | None = None, *, echo: bool = False) -> None:
        """Initialise the async engine and create all tables.

        The *first* call performs initialisation – every subsequent call is a
        no-op (but will log a warning).
        """
        if self.is_connected:
            logger.warning("Database engine already connected – reusing existing engine")
            return

        database_url = database_url or os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable must be set before connecting to the DB")

        # SQLAlchemy async engines expect an async driver (e.g. asyncpg for Postgres)
        # If the user provided a sync URL, we attempt to coerce it to async-pg URL.
        if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        logger.debug(f"Creating async SQLAlchemy engine (echo={echo})")
        self._engine = create_async_engine(database_url, echo=echo, future=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

        # Create tables (equivalent to `prisma db push` for now – migrations will
        # be handled by Alembic, but auto-create helps during development & tests).
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Successfully connected to database via SQLModel/SQLAlchemy")

    async def disconnect(self) -> None:
        """Dispose the engine and tear-down the connection pool."""
        if not self.is_connected:
            logger.warning("Database engine not connected – nothing to disconnect")
            return

        assert self._engine is not None  # mypy
        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("Disconnected from database")

    # ------------------------------------------------------------------
    # Session / transaction helpers
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Return an async SQLAlchemy session context-manager."""
        if not self.is_connected:
            raise RuntimeError("Database engine not initialised – call connect() first")
        assert self._session_factory is not None  # mypy
        async with self._session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession]:
        """Synonym for :pyfunc:`session` – kept for API parity."""
        async with self.session() as sess:
            yield sess


# A *process-level* singleton instance – mirrors the old behaviour
# where the Prisma client lived at ``tux.database.client.db``.

db = DatabaseClient()
