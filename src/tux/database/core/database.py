from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Iterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Session, SQLModel, create_engine


class DatabaseManager:
    def __init__(self, database_url: str, echo: bool = False):
        self.is_async = database_url.startswith(("postgresql+asyncpg", "sqlite+aiosqlite"))
        if self.is_async:
            self.engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
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

    def create_tables(self) -> None:
        SQLModel.metadata.create_all(self.engine)