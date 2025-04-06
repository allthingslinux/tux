"""Database commands for the Tux CLI."""

from collections.abc import Callable
from typing import TypeVar

from tux.cli.core import command_registration_decorator, create_group

# Type for command functions
T = TypeVar("T")
CommandFunction = Callable[[], int]


# Create the database command group
db_group = create_group("db", "Database management commands")


@command_registration_decorator(db_group, name="generate")
def generate() -> int:
    """Generate Prisma client."""

    from tux.cli.impl.database import db_generate

    return db_generate()


@command_registration_decorator(db_group, name="push")
def push() -> int:
    """Push schema changes to database."""

    from tux.cli.impl.database import db_push

    return db_push()


@command_registration_decorator(db_group, name="pull")
def pull() -> int:
    """Pull schema from database."""

    from tux.cli.impl.database import db_pull

    return db_pull()


@command_registration_decorator(db_group, name="migrate")
def migrate() -> int:
    """Run database migrations."""

    from tux.cli.impl.database import db_migrate

    return db_migrate()


@command_registration_decorator(db_group, name="reset")
def reset() -> int:
    """Reset database."""

    from tux.cli.impl.database import db_reset

    return db_reset()
