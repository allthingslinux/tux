"""Database management implementations for Tux."""

import os

from loguru import logger

from tux.cli.impl.core import run_command
from tux.utils.env import get_database_url


def _run_prisma_command(args: list[str], env: dict[str, str]) -> int:
    """
    Run a Prisma command directly.

    When using 'poetry run tux', the prisma binary is already
    properly configured, so we can run it directly.
    """

    logger.info(f"Using database URL: {env['DATABASE_URL']}")

    # Set the environment variables for the process
    env_vars = os.environ | env

    # Use prisma directly - it's already available through Poetry
    try:
        logger.info(f"Running: prisma {' '.join(args)}")
        return run_command(["prisma", *args], env=env_vars)

    except Exception as e:
        logger.error(f"Error running prisma command: {e}")
        return 1


def db_generate() -> int:
    """Generate Prisma client."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["generate"], env=env)


def db_push() -> int:
    """Push database schema changes."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["db", "push"], env=env)


def db_pull() -> int:
    """Pull database schema changes."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["db", "pull"], env=env)


def db_migrate() -> int:
    """Run database migrations."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["migrate", "dev"], env=env)


def db_reset() -> int:
    """Reset database."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["migrate", "reset"], env=env)
