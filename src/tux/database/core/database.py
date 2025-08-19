from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import tux.database.models  # noqa: F401


class DatabaseManager:
    def __init__(self, database_url: str, echo: bool = False):
        # Eagerly import models to register all SQLModel/SQLAlchemy mappings
        # in a single, centralized place to avoid forward-ref resolution issues.
        self.engine: AsyncEngine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
        self.async_session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        # Deprecated: migrations manage schema. Kept for backward compatibility; no-op.
        return None
