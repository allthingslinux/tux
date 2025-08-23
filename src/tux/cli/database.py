"""Database commands for the Tux CLI."""

import asyncio
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import click
from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from tux.cli.core import command_registration_decorator, create_group
from tux.shared.config.env import get_database_url

# Type for command functions
T = TypeVar("T")
CommandFunction = Callable[[], int]


def _create_alembic_config() -> Config:
    """Create an Alembic Config object with pyproject.toml configuration."""
    # Create config with pyproject.toml support
    config = Config(toml_file="pyproject.toml")

    # Set the database URL from environment
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)

    logger.info(f"Using database URL: {database_url}")
    return config


async def _create_database_schema() -> None:
    """Create database schema using SQLAlchemy."""
    database_url = get_database_url()
    engine = create_async_engine(database_url)

    async def create_schema():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()

    await create_schema()


def _run_alembic_command(command_name: str, *args: Any, **kwargs: Any) -> int:
    """
    Run an Alembic command programmatically using the Python API.

    Args:
        command_name: Name of the Alembic command to run
        *args: Positional arguments for the command
        **kwargs: Keyword arguments for the command

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        config = _create_alembic_config()

        # Get the command function from alembic.command module
        command_func = getattr(command, command_name)

        logger.info(f"Running: alembic {command_name} {' '.join(map(str, args))}")
        command_func(config, *args, **kwargs)
    except Exception as e:
        logger.error(f"Error running alembic {command_name}: {e}")
        return 1
    else:
        return 0


# Create the database command group
db_group = create_group("db", "Database management commands")


@command_registration_decorator(db_group, name="upgrade")
def upgrade() -> int:
    """Upgrade database to the latest migration."""
    return _run_alembic_command("upgrade", "head")


@command_registration_decorator(db_group, name="downgrade")
def downgrade() -> int:
    """Downgrade database by one migration."""
    return _run_alembic_command("downgrade", "-1")


@command_registration_decorator(db_group, name="revision")
def revision() -> int:
    """Create a new migration revision."""
    return _run_alembic_command("revision", autogenerate=True)


@command_registration_decorator(db_group, name="current")
def current() -> int:
    """Show current database migration version."""
    return _run_alembic_command("current")


@command_registration_decorator(db_group, name="history")
def history() -> int:
    """Show migration history."""
    return _run_alembic_command("history")


@command_registration_decorator(db_group, name="reset")
def reset() -> int:
    """Reset database to base (WARNING: This will drop all data)."""
    logger.warning("This will reset the database and drop all data!")
    return _run_alembic_command("downgrade", "base")


@command_registration_decorator(db_group, name="reset-migrations")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def reset_migrations(force: bool) -> int:
    """Reset all migrations and create a clean baseline (WARNING: This will drop all data and migrations)."""
    if not force:
        logger.warning("🚨 This will:")
        logger.warning("  1. Drop all database data")
        logger.warning("  2. Delete all migration files")
        logger.warning("  3. Create a fresh baseline migration")
        logger.warning("  4. Apply the new migration")

        # Confirm with user
        try:
            confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
            if confirm.lower() != "yes":
                logger.info("Operation cancelled")
                return 0
        except KeyboardInterrupt:
            logger.info("\nOperation cancelled")
            return 0
    else:
        logger.info("🚀 Running in force mode, skipping confirmation...")

    # Step 1: Drop all tables (reset database)
    logger.info("Step 1: Resetting database...")
    result = _run_alembic_command("downgrade", "base")
    if result != 0:
        logger.warning("Database reset failed or was already empty, continuing...")

    # Step 2: Remove all migration files
    logger.info("Step 2: Removing all migration files...")
    migrations_dir = Path("src/tux/database/migrations/versions")
    if migrations_dir.exists():
        for file in migrations_dir.glob("*.py"):
            if file.name != "__init__.py":
                logger.debug(f"Removing {file}")
                file.unlink()

        # Clean up __pycache__ if it exists
        pycache_dir = migrations_dir / "__pycache__"
        if pycache_dir.exists():
            shutil.rmtree(pycache_dir)
            logger.debug("Cleaned up __pycache__")

    # Step 3: Create tables using SQLAlchemy, then mark database as current
    logger.info("Step 3: Creating database schema...")

    try:
        asyncio.run(_create_database_schema())
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Failed to create schema: {e}")
        return 1

    # Step 4: Create migration file with autogenerate (now it will detect the difference)
    logger.info("Step 4: Generating migration file...")
    result = _run_alembic_command("revision", autogenerate=True, message="Initial baseline migration")
    if result != 0:
        logger.error("Failed to create migration")
        return 1

    # Step 5: Mark the database as being at the current migration level (stamp it)
    logger.info("Step 5: Marking database as current...")
    result = _run_alembic_command("stamp", "head")
    if result != 0:
        logger.error("Failed to stamp database")
        return 1

    logger.success("✅ Migration reset complete! You now have a clean baseline migration.")
    return 0
