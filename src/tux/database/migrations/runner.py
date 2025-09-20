from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from loguru import logger
import sqlalchemy.exc

from tux.shared.config import CONFIG


def _find_project_root(start: Path) -> Path:
    path = start.resolve()
    for parent in [path, *list(path.parents)]:
        if (parent / "alembic.ini").exists():
            return parent
    # Fallback to current working directory
    return Path.cwd()


def _build_alembic_config() -> Config:
    root = _find_project_root(Path(__file__))
    cfg = Config(str(root / "alembic.ini"))

    # Set all required Alembic configuration options
    cfg.set_main_option("sqlalchemy.url", CONFIG.get_database_url())
    cfg.set_main_option("script_location", "src/tux/database/migrations")
    cfg.set_main_option("version_locations", "src/tux/database/migrations/versions")
    cfg.set_main_option("prepend_sys_path", "src")
    cfg.set_main_option("file_template", "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s")
    cfg.set_main_option("timezone", "UTC")

    return cfg


def _run_alembic_command(operation: str, target: str = "head") -> int:  # pyright: ignore[reportUnusedFunction]
    """Run an Alembic migration command.

    Args:
        operation: The migration operation ('upgrade', 'downgrade', 'current', 'history', 'revision')
        target: The target revision for the operation

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        cfg = _build_alembic_config()

        if operation == "upgrade":
            command.upgrade(cfg, target)
            logger.info(f"✅ Successfully upgraded to {target}")
        elif operation == "downgrade":
            command.downgrade(cfg, target)
            logger.info(f"✅ Successfully downgraded to {target}")
        elif operation == "current":
            command.current(cfg)
            logger.info("✅ Current migration version displayed")
        elif operation == "history":
            command.history(cfg)
            logger.info("✅ Migration history displayed")
        elif operation == "revision":
            command.revision(cfg, target)
            logger.info(f"✅ New revision {target} created")
        else:
            raise ValueError(f"Unknown migration operation: {operation}")

        return 0  # Success

    except Exception as e:
        logger.error(f"❌ Error running migration command '{operation}': {type(e).__name__}: {e}")
        return 1  # Error

async def upgrade_head_if_needed() -> None:
    """Run Alembic upgrade to head on startup.

    This call is idempotent and safe to run on startup.

    Raises:
        ConnectionError: When database connection fails
        RuntimeError: When migration execution fails
    """
    cfg = _build_alembic_config()
    logger.info("🔄 Checking database migrations...")

    try:
        # Check current revision first
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
        raise ConnectionError("Database connection failed during migrations") from e
    except Exception as e:
        logger.error(f"❌ Database migration failed: {type(e).__name__}")
        logger.info("💡 Check database connection settings")
        migration_error_msg = f"Migration execution failed: {e}"
        raise RuntimeError(migration_error_msg) from e
