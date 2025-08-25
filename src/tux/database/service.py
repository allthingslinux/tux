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

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import sentry_sdk
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

import tux.database.models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from tux.shared.config.env import get_database_url


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
            future=True,  # Enable SQLAlchemy 2.0 style
            # Connection pooling configuration
            pool_pre_ping=True,  # Verify connections before use
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,  # Connection timeout
            pool_recycle=1800,  # Recycle connections after 30 minutes
            connect_args=connect_args,
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
            await conn.run_sync(SQLModel.metadata.create_all)
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
    # Utility Methods
    # =====================================================================

    async def execute_query(self, operation: Callable[[AsyncSession], Any], span_desc: str) -> Any:
        """Run operation inside a managed session & sentry span (if enabled)."""
        if sentry_sdk.is_initialized():
            with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                span.set_tag("db.service", "DatabaseService")
                try:
                    async with self.session() as session:
                        result = await operation(session)
                    span.set_status("ok")
                except Exception as exc:
                    span.set_status("internal_error")
                    span.set_data("error", str(exc))
                    logger.error(f"{span_desc}: {exc}")
                    raise
                else:
                    return result
        else:
            async with self.session() as session:
                return await operation(session)

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute callback inside a database session / transaction block."""
        try:
            async with self.transaction():
                return await callback()
        except Exception as exc:
            logger.error(f"Transaction failed: {exc}")
            raise

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the async engine for testing purposes."""
        return self._engine

    # Legacy compatibility
    @property
    def manager(self) -> DatabaseService:
        """Legacy compatibility - return self as manager."""
        return self
