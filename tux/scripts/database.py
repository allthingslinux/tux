"""Database management scripts for Tux."""

from tux.scripts.core import run_command


def db_generate() -> int:
    """Generate Prisma client."""
    return run_command(["prisma", "generate"])


def db_push() -> int:
    """Push database schema changes."""
    return run_command(["prisma", "db", "push"])


def db_pull() -> int:
    """Pull database schema changes."""
    return run_command(["prisma", "db", "pull"])


def db_migrate() -> int:
    """Run database migrations."""
    return run_command(["prisma", "migrate", "dev"])


def db_reset() -> int:
    """Reset database."""
    return run_command(["prisma", "migrate", "reset"])
