"""Database setup service for bot initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tux.core.setup.base import BaseSetupService
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxDatabaseConnectionError

if TYPE_CHECKING:
    pass


class DatabaseSetupService(BaseSetupService):
    """Handles database connection and table creation during bot setup."""

    def __init__(self, db_service: DatabaseService) -> None:
        super().__init__("database")
        self.db_service = db_service

    async def setup(self) -> None:
        """Set up and validate the database connection."""
        self._log_step("Connecting to database...")

        await self.db_service.connect(CONFIG.database_url)

        if not self.db_service.is_connected():
            msg = "Database connection test failed"
            raise TuxDatabaseConnectionError(msg)

        self._log_step("Database connected successfully", "success")
        await self._create_tables()

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            from sqlmodel import SQLModel  # noqa: PLC0415

            if engine := self.db_service.engine:
                self._log_step("Creating database tables...")
                if hasattr(engine, "begin"):  # Async engine
                    async with engine.begin() as conn:
                        await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
                else:  # Sync engine
                    SQLModel.metadata.create_all(engine, checkfirst=True)  # type: ignore
                self._log_step("Database tables created/verified", "success")
        except Exception as table_error:
            self._log_step(f"Could not create tables: {table_error}", "warning")
