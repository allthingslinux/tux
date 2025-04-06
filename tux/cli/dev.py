"""Development tools and utilities for Tux."""

from tux.cli.core import command_registration_decorator, create_group

# Create the dev command group
dev_group = create_group("dev", "Development tools")


@command_registration_decorator(dev_group, name="lint")
def lint() -> int:
    """Run linting with Ruff."""
    from tux.cli.impl.dev import lint as run_lint

    return run_lint()


@command_registration_decorator(dev_group, name="lint-fix")
def lint_fix() -> int:
    """Run linting with Ruff and apply fixes."""
    from tux.cli.impl.dev import lint_fix as run_lint_fix

    return run_lint_fix()


@command_registration_decorator(dev_group, name="format")
def format_code() -> int:
    """Format code with Ruff."""
    from tux.cli.impl.dev import format_code as run_format_code

    return run_format_code()


@command_registration_decorator(dev_group, name="type-check")
def type_check() -> int:
    """Check types with Pyright."""
    from tux.cli.impl.dev import type_check as run_type_check

    return run_type_check()


@command_registration_decorator(dev_group, name="pre-commit")
def check() -> int:
    """Run pre-commit checks."""
    from tux.cli.impl.dev import pre_commit as run_check

    return run_check()
