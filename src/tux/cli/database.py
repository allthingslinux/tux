"""Database commands for the Tux CLI."""

import os
from collections.abc import Callable
from typing import TypeVar

from loguru import logger

from tux.cli.core import command_registration_decorator, create_group, run_command
from tux.shared.config.env import get_database_url

# Type for command functions
T = TypeVar("T")
CommandFunction = Callable[[], int]


def _run_alembic_command(args: list[str], env: dict[str, str]) -> int:
    """
    Run an Alembic command for database migrations.

    Args:
        args: List of command arguments to pass to Alembic
        env: Environment variables to set for the command

    Returns:
        Exit code from the command (0 for success, non-zero for failure)
    """
    logger.info(f"Using database URL: {env['DATABASE_URL']}")

    # Set the environment variables for the process
    env_vars = os.environ | env

    # Set PYTHONPATH to include src directory so Alembic can find models
    env_vars["PYTHONPATH"] = f"src:{env_vars.get('PYTHONPATH', '')}"

    try:
        logger.info(f"Running: alembic {' '.join(args)}")
        return run_command(["alembic", "-c", "alembic.ini", *args], env=env_vars)

    except Exception as e:
        logger.error(f"Error running alembic command: {e}")
        return 1


# Create the database command group
db_group = create_group("db", "Database management commands")


@command_registration_decorator(db_group, name="upgrade")
def upgrade() -> int:
    """Upgrade database to the latest migration."""
    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["upgrade", "head"], env=env)


@command_registration_decorator(db_group, name="downgrade")
def downgrade() -> int:
    """Downgrade database by one migration."""
    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["downgrade", "-1"], env=env)


@command_registration_decorator(db_group, name="revision")
def revision() -> int:
    """Create a new migration revision."""
    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["revision", "--autogenerate"], env=env)


@command_registration_decorator(db_group, name="current")
def current() -> int:
    """Show current database migration version."""
    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["current"], env=env)


@command_registration_decorator(db_group, name="history")
def history() -> int:
    """Show migration history."""
    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["history"], env=env)


@command_registration_decorator(db_group, name="reset")
def reset() -> int:
    """Reset database to base (WARNING: This will drop all data)."""
    env = {"DATABASE_URL": get_database_url()}
    logger.warning("This will reset the database and drop all data!")
    return _run_alembic_command(["downgrade", "base"], env=env)
