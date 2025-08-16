from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlmodel import SQLModel

from tux.database.core.database import DatabaseManager
from tux.shared.config.env import get_database_url


class DatabaseService:
    def __init__(self, echo: bool = False):
        self.manager = DatabaseManager(get_database_url(), echo=echo)

    @asynccontextmanager
    async def session(self):
        async with self.manager.get_session() as s:  # type: ignore[reportUnknownMemberType]
            yield s

    def create_all(self) -> None:
        self.manager.create_tables()