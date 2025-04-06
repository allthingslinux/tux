"""Development tools and utilities for Tux."""

from tux.cli.impl.core import run_command


def lint() -> int:
    """Run linting with Ruff."""

    return run_command(["ruff", "check", "."])


def lint_fix() -> int:
    """Run linting with Ruff and apply fixes."""

    return run_command(["ruff", "check", "--fix", "."])


def format_code() -> int:
    """Format code with Ruff."""

    return run_command(["ruff", "format", "."])


def type_check() -> int:
    """Check types with Pyright."""

    return run_command(["pyright"])


def pre_commit() -> int:
    """Run pre-commit checks."""

    return run_command(["pre-commit", "run", "--all-files"])
