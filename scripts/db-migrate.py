#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

from tux.shared.config.env import get_database_url


def setup_environment():
    """Setup environment variables."""
    mode = os.getenv("MODE", "dev")
    os.environ["MODE"] = mode

    try:
        db_url = get_database_url()
        os.environ["DATABASE_URL"] = db_url
        logger.info(f"Running in {mode} mode")
        logger.info(f"Database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    except Exception as e:
        logger.error(f"❌ Failed to configure database: {e}")
        sys.exit(1)


async def run_migration_command(command: str, **kwargs: Any):
    """Run a migration command."""
    import alembic.command as alembic_cmd  # noqa: PLC0415
    from alembic.config import Config  # noqa: PLC0415

    # Create alembic config
    config = Config()
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
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
        elif command == "reset":
            logger.warning("⚠️  Resetting database...")
            alembic_cmd.downgrade(config, "base")
        elif command == "reset-migrations":
            logger.warning("⚠️  Resetting migrations...")
            # This is complex, would need more implementation
            logger.error("❌ reset-migrations not implemented in simple script")
            return 1
        else:
            logger.error(f"❌ Unknown command: {command}")
            return 1

        logger.success(f"✅ {command} completed successfully")
    except Exception as e:
        logger.error(f"❌ {command} failed: {e}")
        return 1
    else:
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("❌ No command specified")
        sys.exit(1)

    command = sys.argv[1]
    setup_environment()

    if command in ["upgrade", "downgrade", "revision", "current", "history", "reset"]:
        exit_code = asyncio.run(run_migration_command(command))
        sys.exit(exit_code)
    else:
        logger.error(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
