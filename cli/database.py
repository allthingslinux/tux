"""Database commands for the Tux CLI."""

import os
from collections.abc import Callable
from typing import TypeVar

from loguru import logger
from utils.env import get_database_url

from cli.core import command_registration_decorator, create_group, run_command

# Type for command functions
T = TypeVar("T")
CommandFunction = Callable[[], int]


# Helper function moved from impl/database.py
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


# Create the database command group
db_group = create_group("db", "Database management commands")


@command_registration_decorator(db_group, name="generate")
def generate() -> int:
    """Generate Prisma client."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["generate"], env=env)


@command_registration_decorator(db_group, name="push")
def push() -> int:
    """Push schema changes to database."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["db", "push"], env=env)


@command_registration_decorator(db_group, name="pull")
def pull() -> int:
    """Pull schema from database."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["db", "pull"], env=env)


@command_registration_decorator(db_group, name="migrate")
def migrate() -> int:
    """Run database migrations."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["migrate", "dev"], env=env)


@command_registration_decorator(db_group, name="reset")
def reset() -> int:
    """Reset database."""

    env = {"DATABASE_URL": get_database_url()}
    return _run_prisma_command(["migrate", "reset"], env=env)
