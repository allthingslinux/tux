#!/usr/bin/env python3
"""
Tux Database Management Script
Comprehensive database management tool for Tux bot

Usage:
    python scripts/db.py <command>

Commands:
    test          Test database connection
    init          Initialize database schema
    upgrade       Upgrade to latest migration
    current       Show current migration
    downgrade     Downgrade by one migration
    reset         Reset to base state (DANGER!)
    revision      Create new migration revision
"""

import argparse
import asyncio
import os
import sys
import traceback
from typing import NoReturn, overload

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tux.database.service import DatabaseService
from tux.shared.config.env import configure_environment, get_database_url


def create_alembic_config():
    """Create an Alembic Config object with proper configuration.

    Reads configuration from alembic.ini file in the root directory.
    """
    # Create config from alembic.ini file
    config = Config("alembic.ini")

    # Override the database URL from environment (this should still be dynamic)
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)

    return config


def get_mode_info():
    """Get current mode information for logging."""
    return os.environ.get("MODE", "dev")


@overload
def log_mode_info() -> str: ...


@overload
def log_mode_info(include_dev_mode: bool) -> tuple[str, bool]: ...


def log_mode_info(include_dev_mode: bool = False) -> tuple[str, bool] | str:
    """Log mode information and return mode details.

    Args:
        include_dev_mode: Whether to return dev_mode boolean as well

    Returns:
        If include_dev_mode is True, returns (mode, dev_mode) tuple
        Otherwise returns just mode string
    """
    mode = get_mode_info()
    if include_dev_mode:
        dev_mode = mode == "dev"
        logger.info(f"🔧 Mode: {mode} (dev_mode={dev_mode})")
        return mode, dev_mode

    logger.info(f"🔧 Mode: {mode}")
    return mode


async def test_connection() -> bool:
    """Test database connection."""
    try:
        # Get mode from environment
        _, dev_mode = log_mode_info(include_dev_mode=True)

        configure_environment(dev_mode=dev_mode)
        database_url = get_database_url()
        logger.info(f"📍 Using database URL: {database_url}")

        engine = create_async_engine(database_url)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row is not None:
                logger.success(f"✅ Database connection successful! Test result: {row[0]}")
                await engine.dispose()
                return True
            logger.error("❌ Database query returned no results")
            await engine.dispose()
            return False

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def init_database() -> bool:
    """Initialize database schema."""
    try:
        # Get mode from environment
        _, dev_mode = log_mode_info(include_dev_mode=True)

        configure_environment(dev_mode=dev_mode)
        db_service = DatabaseService()
        await db_service.connect()
        await db_service.create_tables()
        await db_service.disconnect()

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        logger.error(traceback.format_exc())
        return False
    else:
        logger.success("✅ Database schema initialized")
        return True


def upgrade_database() -> bool:
    """Upgrade database to latest migration."""
    try:
        # Get mode information
        log_mode_info()

        config = create_alembic_config()
        logger.info(f"📍 Using database URL: {config.get_main_option('sqlalchemy.url')}")

        logger.info("⬆️  Upgrading database to latest migration...")
        command.upgrade(config, "head")

    except Exception as e:
        logger.error(f"❌ Error upgrading database: {e}")
        logger.error(traceback.format_exc())
        return False
    else:
        logger.success("✅ Database upgrade completed")
        return True


def show_current() -> bool:
    """Get current migration version."""
    try:
        # Get mode information
        log_mode_info()

        config = create_alembic_config()
        logger.info(f"📍 Using database URL: {config.get_main_option('sqlalchemy.url')}")
        logger.info(f"📁 Script location: {config.get_main_option('script_location')}")

        logger.info("🔍 Checking current migration...")
        command.current(config)

    except Exception as e:
        logger.error(f"❌ Error getting current migration: {e}")
        logger.error(traceback.format_exc())
        return False
    else:
        logger.success("✅ Current migration check completed")
        return True


def downgrade_database() -> bool:
    """Downgrade database by one migration."""
    try:
        # Get mode information
        log_mode_info()

        config = create_alembic_config()
        logger.info(f"📍 Using database URL: {config.get_main_option('sqlalchemy.url')}")

        logger.info("⬇️  Downgrading database by one migration...")
        command.downgrade(config, "-1")

    except Exception as e:
        logger.error(f"❌ Error downgrading database: {e}")
        logger.error(traceback.format_exc())
        return False
    else:
        logger.success("✅ Database downgrade completed")
        return True


def reset_database() -> bool:
    """Reset database to base state."""
    try:
        # Get mode information
        log_mode_info()

        config = create_alembic_config()
        logger.info(f"📍 Using database URL: {config.get_main_option('sqlalchemy.url')}")

        logger.info("🔄 Resetting database to base state...")
        logger.warning("⚠️  This will destroy all data!")

        # Downgrade to base (removes all migrations)
        command.downgrade(config, "base")

    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")
        logger.error(traceback.format_exc())
        return False
    else:
        logger.success("✅ Database reset to base state")
        return True


def create_revision() -> bool:
    """Create new migration revision."""
    try:
        # Get mode information
        log_mode_info()

        config = create_alembic_config()
        logger.info(f"📍 Using database URL: {config.get_main_option('sqlalchemy.url')}")

        logger.info("📝 Creating new migration revision...")
        command.revision(config, autogenerate=True, message="Auto-generated migration")

    except Exception as e:
        logger.error(f"❌ Error creating migration: {e}")
        logger.error(traceback.format_exc())
        return False
    else:
        logger.success("✅ Migration revision created")
        return True


def main() -> NoReturn:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Tux Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python scripts/db.py test          # Test database connection
  uv run python scripts/db.py init          # Initialize database schema
  uv run python scripts/db.py upgrade       # Upgrade to latest migration
  uv run python scripts/db.py current       # Show current migration
  uv run python scripts/db.py downgrade     # Downgrade by one migration
  uv run python scripts/db.py reset         # Reset to base state (DANGER!)
  uv run python scripts/db.py revision      # Create new migration revision
        """,
    )

    parser.add_argument(
        "command",
        choices=["test", "init", "upgrade", "current", "downgrade", "reset", "revision"],
        help="Database operation to perform",
    )

    args = parser.parse_args()

    # Execute the requested command
    if args.command == "test":
        success = asyncio.run(test_connection())
    elif args.command == "init":
        success = asyncio.run(init_database())
    elif args.command == "upgrade":
        success = upgrade_database()
    elif args.command == "current":
        success = show_current()
    elif args.command == "downgrade":
        success = downgrade_database()
    elif args.command == "reset":
        success = reset_database()
    elif args.command == "revision":
        success = create_revision()
    else:
        logger.error(f"Unknown command: {args.command}")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

    database_url = get_database_url()
