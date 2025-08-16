from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Session, SQLModel, create_engine


class DatabaseManager:
    def __init__(self, database_url: str, echo: bool = False):
        self.is_async = database_url.startswith(("postgresql+asyncpg", "sqlite+aiosqlite"))
        if self.is_async:
            self.engine: AsyncEngine | Any = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
            self.async_session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self.engine = create_engine(database_url, echo=echo, pool_pre_ping=True)

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
            with Session(self.engine) as session:  # type: ignore[arg-type]
                try:
                    yield session
                    session.commit()
                except Exception:
                    session.rollback()
                    raise

    async def create_tables_async(self) -> None:
        if not self.is_async:
            SQLModel.metadata.create_all(self.engine)
            return
        async with self.engine.begin() as conn:  # type: ignore[reportAttributeAccessIssue]
            await conn.run_sync(SQLModel.metadata.create_all)

    def create_tables(self) -> None:
        # Synchronous convenience wrapper
        if self.is_async:
            raise RuntimeError("Use create_tables_async() with async engines")
        SQLModel.metadata.create_all(self.engine)