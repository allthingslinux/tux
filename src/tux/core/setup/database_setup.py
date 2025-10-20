"""Database setup service for bot initialization."""

from __future__ import annotations

import io
from pathlib import Path

import sqlalchemy.exc
from alembic import command
from alembic.config import Config
from loguru import logger
from sqlmodel import SQLModel

from tux.core.setup.base import BaseSetupService
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxDatabaseConnectionError


class DatabaseSetupService(BaseSetupService):
    """Handles complete database initialization during bot setup."""

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize the database setup service.

        Parameters
        ----------
        db_service : DatabaseService
            The database service instance to use for connections.
        """
        super().__init__("database")
        self.db_service = db_service

    def _find_project_root(self) -> Path:
        """Find the project root by looking for alembic.ini."""
        path = Path(__file__).resolve()
        for parent in [path, *list(path.parents)]:
            if (parent / "alembic.ini").exists():
                return parent
        # Fallback to current working directory
        return Path.cwd()

    def _build_alembic_config(self) -> Config:
        """Build Alembic configuration with suppressed stdout output.

        Notes
        -----
        Most configuration is read from alembic.ini. Only the database URL
        is set programmatically as it comes from environment variables.
        """
        root = self._find_project_root()

        # Suppress Alembic's stdout output by redirecting to StringIO
        cfg = Config(str(root / "alembic.ini"), stdout=io.StringIO())

        # Override database URL with runtime configuration from environment
        cfg.set_main_option("sqlalchemy.url", CONFIG.database_url)

        return cfg

    async def _upgrade_head_if_needed(self) -> None:
        """Run Alembic upgrade to head on startup.

        This call is idempotent and safe to run on startup.
        """
        cfg = self._build_alembic_config()
        logger.info("🔄 Checking database migrations...")

        try:
            # Check current revision first (stdout already suppressed via Config)
            current_rev = command.current(cfg)
            logger.debug(f"Current database revision: {current_rev}")

            # Check if we need to upgrade
            head_rev = command.heads(cfg)
            logger.debug(f"Head revision: {head_rev}")

            # Only run upgrade if we're not already at head
            if current_rev != head_rev:
                logger.info("🔄 Running database migrations...")
                command.upgrade(cfg, "head")
                logger.info("✅ Database migrations completed")
            else:
                logger.info("✅ Database is already up to date")

        except sqlalchemy.exc.OperationalError as e:
            logger.error("❌ Database migration failed: Cannot connect to database")
            logger.info("💡 Ensure PostgreSQL is running: make docker-up")
            msg = "Database connection failed during migrations"
            raise ConnectionError(msg) from e

        except Exception as e:
            logger.error(f"❌ Database migration failed: {type(e).__name__}")
            logger.info("💡 Check database connection settings")
            migration_error_msg = f"Migration execution failed: {e}"
            raise RuntimeError(migration_error_msg) from e

    async def setup(self) -> None:
        """Set up and validate the database connection and run migrations."""
        self._log_step("Connecting to database...")

        await self.db_service.connect(CONFIG.database_url)

        if not self.db_service.is_connected():
            msg = "Database connection test failed"
            raise TuxDatabaseConnectionError(msg)

        self._log_step("Database connected successfully", "success")
        await self._create_tables()
        await self._upgrade_head_if_needed()

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            if engine := self.db_service.engine:
                self._log_step("Creating database tables...")

                async with engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)

                self._log_step("Database tables created/verified", "success")

        except Exception as table_error:
            self._log_step(f"Could not create tables: {table_error}", "warning")
