"""Database setup service for bot initialization."""

from __future__ import annotations

import asyncio
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlmodel import SQLModel

from tux.core.setup.base import BaseSetupService
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG
from tux.shared.exceptions import (
    TuxDatabaseConnectionError,
    TuxDatabaseMigrationError,
    TuxSetupError,
)

__all__ = ["DatabaseSetupService"]


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
        """
        Find the project root by looking for alembic.ini.

        Returns
        -------
        Path
            The project root directory containing alembic.ini.
        """
        path = Path(__file__).resolve()
        for parent in [path, *list(path.parents)]:
            if (parent / "alembic.ini").exists():
                return parent
        # Fallback to current working directory
        return Path.cwd()

    def _build_alembic_config(self) -> Config:
        """
        Build Alembic configuration with suppressed stdout output.

        Most configuration is read from alembic.ini. Only the database URL
        is set programmatically as it comes from environment variables.

        Returns
        -------
        Config
            The configured Alembic Config object.
        """
        root = self._find_project_root()

        # Suppress Alembic's stdout output by redirecting to StringIO
        cfg = Config(str(root / "alembic.ini"), stdout=io.StringIO())

        # Override database URL with runtime configuration from environment
        cfg.set_main_option("sqlalchemy.url", CONFIG.database_url)

        return cfg

    async def _upgrade_head_if_needed(self) -> None:
        """
        Run Alembic upgrade to head on startup.

        This call is idempotent and safe to run on startup. Runs migration
        synchronously with a timeout. If migrations fail for any reason (database
        unavailable, migration errors, timeout), this method raises an exception
        to prevent the bot from starting with an inconsistent database state.

        Raises
        ------
        TuxDatabaseMigrationError
            If database is unavailable, migrations fail, or migration check times out.
        """
        cfg = self._build_alembic_config()
        logger.info("Checking database migrations...")

        loop = asyncio.get_event_loop()

        # Database is available (already connected in setup()),
        # run migrations with a timeout
        def _run_migration_sync():
            try:
                # Check current revision first (stdout already suppressed via Config)
                current_rev = command.current(cfg)
                logger.debug(f"Current database revision: {current_rev}")

                # Check if we need to upgrade
                head_rev = command.heads(cfg)
                logger.debug(f"Head revision: {head_rev}")

                # Only run upgrade if we're not already at head
                if current_rev != head_rev:
                    logger.info("Running database migrations...")
                    # Run the upgrade
                    command.upgrade(cfg, "head")
                    logger.success("Database migrations completed")
                else:
                    logger.success("Database is already up to date")
            except Exception as e:
                error_msg = f"Failed to run database migrations: {e}"
                logger.exception(error_msg)
                raise TuxDatabaseMigrationError(error_msg) from e

        try:
            # Run migrations with a timeout
            await asyncio.wait_for(
                loop.run_in_executor(None, _run_migration_sync),
                timeout=30.0,  # 30 second timeout for actual migrations
            )
        except TimeoutError as e:
            error_msg = (
                "Migration check timed out after 30 seconds. "
                "Database may be slow or migrations may be blocking. "
                "Run migrations manually with 'uv run db push'"
            )
            logger.exception(error_msg)
            raise TuxDatabaseMigrationError(error_msg) from e
        except TuxDatabaseMigrationError:
            # Re-raise migration errors as-is
            raise
        except Exception as e:
            error_msg = (
                f"Unexpected error during migration check: {e}. "
                "Run migrations manually with 'uv run db push'"
            )
            logger.exception(error_msg)
            raise TuxDatabaseMigrationError(error_msg) from e

    async def setup(self) -> None:
        """
        Set up and validate the database connection and run migrations.

        Raises
        ------
        TuxDatabaseConnectionError
            If database connection or validation fails.
        """
        logger.info("Connecting to database...")

        await self.db_service.connect(CONFIG.database_url)

        if not self.db_service.is_connected():
            msg = "Database connection test failed"
            raise TuxDatabaseConnectionError(msg)

        # Test actual database connectivity with a simple query
        try:
            await self.db_service.test_connection()
        except Exception as e:
            # Error already logged by database service, just raise with context
            error_msg = f"Database connection test failed: {e}"
            raise TuxDatabaseConnectionError(error_msg) from e

        logger.success("Database connected successfully")
        await self._create_tables()
        await self._upgrade_head_if_needed()
        await self._validate_schema()

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            if engine := self.db_service.engine:
                logger.info("Creating database tables...")

                async with engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)

                logger.success("Database tables created/verified")

        except Exception as table_error:
            logger.warning(f"Could not create tables: {table_error}")

    async def _validate_schema(self) -> None:
        """Validate that the database schema matches model definitions."""
        try:
            logger.info("Validating database schema...")

            schema_result = await self.db_service.validate_schema()

            if schema_result["status"] == "valid":
                logger.success("Database schema validation passed")
            else:
                error_msg = schema_result.get(
                    "error",
                    "Unknown schema validation error",
                )
                logger.error(f"Database schema validation failed: {error_msg}")
                msg = f"Schema validation failed: {error_msg}"
                raise TuxSetupError(msg)  # noqa: TRY301

        except Exception as schema_error:
            logger.error(f"Schema validation error: {schema_error}")
            raise
