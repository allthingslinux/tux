# ruff: noqa: T201

"""Database management scripts for Tux."""

import os

from tux.scripts.core import run_command
from tux.utils.config import Config


def _get_database_url() -> str:  # sourcery skip: assign-if-exp, reintroduce-else
    """Get the appropriate database URL based on environment."""
    is_dev = os.environ.get("DEV", "true").lower() == "true"

    # Use Config class which already has the right logic
    if is_dev:
        return Config.DEV_DATABASE_URL

    return Config.PROD_DATABASE_URL


def _run_prisma_command(args: list[str], env: dict[str, str]) -> int:
    """
    Run a Prisma command directly.

    When using 'poetry run tux', the prisma binary is already
    properly configured, so we can run it directly.
    """
    print(f"Using database URL: {env['DATABASE_URL']}")

    # Set the environment variables for the process
    env_vars = os.environ.copy() | env

    # Use prisma directly - it's already available through Poetry
    try:
        print(f"Running: prisma {' '.join(args)}")
        return run_command(["prisma", *args], env=env_vars)
    except Exception as e:
        print(f"Error running prisma command: {e}")
        return 1


def db_generate() -> int:
    """Generate Prisma client."""
    env = {"DATABASE_URL": _get_database_url()}
    return _run_prisma_command(["generate"], env=env)


def db_push() -> int:
    """Push database schema changes."""
    env = {"DATABASE_URL": _get_database_url()}
    return _run_prisma_command(["db", "push"], env=env)


def db_pull() -> int:
    """Pull database schema changes."""
    env = {"DATABASE_URL": _get_database_url()}
    return _run_prisma_command(["db", "pull"], env=env)


def db_migrate() -> int:
    """Run database migrations."""
    env = {"DATABASE_URL": _get_database_url()}
    return _run_prisma_command(["migrate", "dev"], env=env)


def db_reset() -> int:
    """Reset database."""
    env = {"DATABASE_URL": _get_database_url()}
    return _run_prisma_command(["migrate", "reset"], env=env)
