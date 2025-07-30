"""Database commands for the Tux CLI."""

import os
from collections.abc import Callable
from typing import TypeVar

from loguru import logger

from tux.cli.core import command_registration_decorator, create_group, run_command
from tux.utils.env import get_database_url

# Type for command functions
T = TypeVar("T")
CommandFunction = Callable[[], int]


def _run_alembic_command(args: list[str], env: dict[str, str]) -> int:
    """Run an Alembic command with the provided environment variables."""

    logger.info(f"Using database URL: {env['DATABASE_URL']}")

    env_vars = os.environ | env

    try:
        logger.info("Running: alembic %s", " ".join(args))
        return run_command(["alembic", *args], env=env_vars)
    except Exception as exc:
        logger.error("Error running alembic command: %s", exc)
        return 1


# ---------------------------------------------------------------------------
# Command group
# ---------------------------------------------------------------------------

db_group = create_group("db", "Database migration commands (Alembic)")


# ---------------------------------------------------------------------------
# Alembic command wrappers
# ---------------------------------------------------------------------------


@command_registration_decorator(db_group, name="upgrade")
def upgrade() -> int:
    """Apply all pending migrations (alembic upgrade head)."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["upgrade", "head"], env=env)


@command_registration_decorator(db_group, name="downgrade")
def downgrade() -> int:
    """Downgrade one migration step (alembic downgrade -1)."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["downgrade", "-1"], env=env)


@command_registration_decorator(db_group, name="revision")
def revision() -> int:
    """Create a new migration autogenerating from model changes."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["revision", "--autogenerate", "-m", "auto"], env=env)


@command_registration_decorator(db_group, name="current")
def current() -> int:
    """Show current migration revision."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["current"], env=env)


@command_registration_decorator(db_group, name="history")
def history() -> int:
    """Show migration history."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_alembic_command(["history"], env=env)
