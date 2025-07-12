"""Development tools and utilities for Tux."""

from cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)

# Create the dev command group
dev_group = create_group("dev", "Development tools")


@command_registration_decorator(dev_group, name="lint")
def lint() -> int:
    """Run linting with Ruff."""
    return run_command(["ruff", "check", "."])


@command_registration_decorator(dev_group, name="lint-fix")
def lint_fix() -> int:
    """Run linting with Ruff and apply fixes."""
    return run_command(["ruff", "check", "--fix", "."])


@command_registration_decorator(dev_group, name="format")
def format_code() -> int:
    """Format code with Ruff."""
    return run_command(["ruff", "format", "."])


@command_registration_decorator(dev_group, name="type-check")
def type_check() -> int:
    """Check types with Pyright."""
    return run_command(["pyright"])


@command_registration_decorator(dev_group, name="pre-commit")
def check() -> int:
    """Run pre-commit checks."""
    return run_command(["pre-commit", "run", "--all-files"])
