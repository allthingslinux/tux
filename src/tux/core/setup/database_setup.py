"""Database setup service for bot initialization."""

from __future__ import annotations

import asyncio
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from loguru import logger
from sqlalchemy import text
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

    async def _get_current_revision(self) -> str | None:
        """Get current database revision by querying alembic_version table.

        Returns
        -------
        str | None
            Current revision string, or None if no migrations applied.
        """
        try:
            async with self.db_service.session() as session:
                result = await session.execute(
                    text("SELECT version_num FROM alembic_version"),
                )
                row = result.fetchone()
                return row[0] if row else None
        except Exception:
            # Table doesn't exist or query failed - no migrations applied yet
            return None

    async def _check_tables_exist(self) -> bool:
        """Check if any application tables exist in the database.

        Returns
        -------
        bool
            True if tables exist, False otherwise.
        """
        try:
            async with self.db_service.session() as session:
                result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_type = 'BASE TABLE'
                          AND table_name != 'alembic_version'
                        """,
                    ),
                )
                count = result.scalar() or 0
                return count > 0
        except Exception:
            # If query fails, assume no tables exist
            return False

    async def _stamp_database_if_needed(self) -> None:
        """Stamp database with head revision if tables exist but no Alembic version.

        This handles the case where tables were created manually (e.g., via
        SQLModel.metadata.create_all) but Alembic version tracking is missing.
        """
        current_rev = await self._get_current_revision()
        tables_exist = await self._check_tables_exist()

        # If tables exist but no Alembic version, we need to stamp the database
        if tables_exist and current_rev is None:
            logger.warning(
                "Database has tables but no Alembic version. "
                "Stamping database with head revision...",
            )

            cfg = self._build_alembic_config()
            script_dir = ScriptDirectory.from_config(cfg)
            head_revs = [rev.revision for rev in script_dir.get_revisions("head")]

            if not head_revs:
                logger.error("No head revisions found. Cannot stamp database.")
                msg = "Cannot stamp database: no migration head found"
                raise TuxDatabaseMigrationError(msg)

            # Use the first head revision (or comma-separated if multiple)
            head_rev = ",".join(head_revs) if len(head_revs) > 1 else head_revs[0]

            loop = asyncio.get_event_loop()

            def _stamp_sync():
                try:
                    command.stamp(cfg, head_rev)
                    logger.success(f"Database stamped with revision: {head_rev}")
                except Exception as e:
                    error_msg = f"Failed to stamp database: {e}"
                    logger.exception(error_msg)
                    raise TuxDatabaseMigrationError(error_msg) from e

            try:
                await asyncio.wait_for(
                    loop.run_in_executor(None, _stamp_sync),
                    timeout=10.0,
                )
            except TimeoutError as e:
                error_msg = "Database stamping timed out after 10 seconds"
                logger.exception(error_msg)
                raise TuxDatabaseMigrationError(error_msg) from e
            except TuxDatabaseMigrationError:
                raise
            except Exception as e:
                error_msg = f"Unexpected error during database stamping: {e}"
                logger.exception(error_msg)
                raise TuxDatabaseMigrationError(error_msg) from e

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

        # Get current revision from database (more reliable than command.current
        # which can be affected by stdout suppression)
        current_rev = await self._get_current_revision()
        logger.debug(f"Current database revision: {current_rev}")

        # Use ScriptDirectory to reliably get head revisions
        # command.heads() can return None in some cases, but ScriptDirectory is more reliable
        script_dir = ScriptDirectory.from_config(cfg)
        head_revs = [rev.revision for rev in script_dir.get_revisions("head")]
        head_revs_str = ", ".join(head_revs) or "None (no migration files)"
        logger.debug(f"Head revision(s): {head_revs_str}")

        loop = asyncio.get_event_loop()

        # Database is available (already connected in setup()),
        # run migrations with a timeout
        def _run_migration_sync():
            try:
                # Alembic's upgrade command is idempotent - it will:
                # - Create alembic_version table if needed
                # - Only apply migrations that haven't been applied
                # - Do nothing if already at head
                # This matches the pattern used in scripts/db/push.py
                logger.info("Running database migrations...")
                command.upgrade(cfg, "head")
                logger.success("Database migrations completed")
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
        # Check if we need to stamp the database (tables exist but no Alembic version)
        # This handles the case where tables were created manually but Alembic
        # version tracking is missing. Once stamped, Alembic will manage everything.
        await self._stamp_database_if_needed()
        # Run migrations to ensure database is up to date
        # Migrations will create tables if they don't exist, or apply pending changes
        await self._upgrade_head_if_needed()
        await self._validate_schema()

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist.

        Note: This method is deprecated in favor of Alembic migrations.
        It's kept for backward compatibility but should not be called
        when Alembic is managing the database schema.
        """
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
