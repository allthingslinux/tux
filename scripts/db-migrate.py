#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

from tux.shared.config import CONFIG


def setup_environment():
    """Setup environment variables."""
    logger.info("Setting up database migration...")

    # Get configuration
    db_url = CONFIG.get_database_url()

    logger.info(f"Database: {db_url.split('@')[1] if '@' in db_url else 'local'}")


async def reset_migrations():
    """Reset all migrations and create a clean baseline."""
    import alembic.command as alembic_cmd  # noqa: PLC0415
    from alembic.config import Config  # noqa: PLC0415

    # Get configuration
    db_url = CONFIG.get_database_url()

    # Create alembic config
    config = Config()
    config.set_main_option("sqlalchemy.url", db_url)
    config.set_main_option("script_location", "src/tux/database/migrations")
    config.set_main_option("version_locations", "src/tux/database/migrations/versions")
    config.set_main_option("prepend_sys_path", "src")
    config.set_main_option("timezone", "UTC")

    try:
        # Step 1: Drop all database data by downgrading to base
        logger.info("1️⃣ Dropping all database data...")
        alembic_cmd.downgrade(config, "base")

        # Step 2: Delete all migration files
        logger.info("2️⃣ Deleting all migration files...")
        versions_dir = Path("src/tux/database/migrations/versions")
        if versions_dir.exists():
            for migration_file in versions_dir.glob("*.py"):
                if migration_file.name != "__init__.py":
                    migration_file.unlink()
                    logger.info(f"   Deleted: {migration_file.name}")

        # Step 3: Create a fresh baseline migration
        logger.info("3️⃣ Creating fresh baseline migration...")
        alembic_cmd.revision(config, autogenerate=True, message="baseline")

        # Step 4: Apply the new migration
        logger.info("4️⃣ Applying new baseline migration...")
        alembic_cmd.upgrade(config, "head")

        logger.success("✅ Migration reset completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration reset failed: {e}")
        return 1
    else:
        return 0


async def run_migration_command(command: str, **kwargs: Any) -> int:
    """Run a migration command."""
    import alembic.command as alembic_cmd  # noqa: PLC0415
    from alembic.config import Config  # noqa: PLC0415

    # Get configuration
    db_url = CONFIG.get_database_url()

    # Create alembic config
    config = Config()
    config.set_main_option("sqlalchemy.url", db_url)
    config.set_main_option("script_location", "src/tux/database/migrations")
    config.set_main_option("version_locations", "src/tux/database/migrations/versions")
    config.set_main_option("prepend_sys_path", "src")
    config.set_main_option("timezone", "UTC")

    try:
        if command == "upgrade":
            alembic_cmd.upgrade(config, "head")
        elif command == "downgrade":
            alembic_cmd.downgrade(config, "-1")
        elif command == "revision":
            alembic_cmd.revision(config, autogenerate=True)
        elif command == "current":
            alembic_cmd.current(config)
        elif command == "history":
            alembic_cmd.history(config)
        elif command in {"reset", "reset-migrations"}:
            return await reset_migrations()
        else:
            logger.error(f"Unknown command: {command}")
            return 1

        logger.success(f"✅ {command} completed successfully!")

    except Exception as e:
        logger.error(f"❌ {command} failed: {e}")
        return 1

    return 0


async def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("Usage: python db-migrate.py <command>")
        logger.info("Available commands: upgrade, downgrade, revision, current, history, reset")
        return 1

    command = sys.argv[1]
    logger.info(f"Running migration command: {command}")

    # Setup environment
    setup_environment()

    return await run_migration_command(command)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
