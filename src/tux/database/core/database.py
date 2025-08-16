from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Session, SQLModel, create_engine


class DatabaseManager:
    def __init__(self, database_url: str, echo: bool = False):
        self.is_async = database_url.startswith(("postgresql+asyncpg", "sqlite+aiosqlite"))
        self.async_engine: AsyncEngine | None = None
        self.sync_engine: Engine | None = None
        if self.is_async:
            self.async_engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
            self.async_session_factory = async_sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self.sync_engine = create_engine(database_url, echo=echo, pool_pre_ping=True)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession | Session, None]:
        if self.is_async:
            async with self.async_session_factory() as session:  # type: ignore[attr-defined]
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        else:
            assert self.sync_engine is not None
            with Session(self.sync_engine) as session:
                try:
                    yield session
                    session.commit()
                except Exception:
                    session.rollback()
                    raise

    async def create_tables_async(self) -> None:
        if not self.is_async:
            assert self.sync_engine is not None
            SQLModel.metadata.create_all(self.sync_engine)
            return
        assert self.async_engine is not None
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    def create_tables(self) -> None:
        if self.is_async:
            raise RuntimeError("Use create_tables_async() with async engines")
        assert self.sync_engine is not None
        SQLModel.metadata.create_all(self.sync_engine)