"""Development and utility scripts for Tux."""

import subprocess
from typing import Any


def run_command(cmd: list[str], **kwargs: Any) -> int:
    """Run a command and return its exit code.

    Parameters
    ----------
    cmd : list[str]
        Command to run as a list of strings
    **kwargs : Any
        Additional arguments to pass to subprocess.run

    Returns
    -------
    int
        Exit code of the command (0 for success)
    """
    try:
        subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        return e.returncode
    else:
        return 0


def lint() -> int:
    """Run Ruff linter."""
    return run_command(["ruff", "check", "."])


def lint_fix() -> int:
    """Run Ruff linter with auto-fix."""
    return run_command(["ruff", "check", "--fix", "."])


def format_code() -> int:
    """Format the codebase using Ruff."""
    return run_command(["ruff", "format", "."])


def typecheck() -> int:
    """Run Pyright type checker."""
    return run_command(["pyright"])


def check() -> int:
    """Run pre-commit checks."""
    return run_command(["pre-commit", "run", "--all-files"])


def docs() -> int:
    """Serve documentation locally."""
    return run_command(["mkdocs", "serve", "-f", "docs/mkdocs.yml"])


def docs_build() -> int:
    """Build documentation site."""
    return run_command(["mkdocs", "build"])


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
