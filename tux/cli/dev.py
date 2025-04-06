"""Development commands for the Tux CLI."""

from tux.cli.core import command_registration_decorator, create_group

# Create the development command group
dev_group = create_group("dev", "Development tools and commands")


@command_registration_decorator(dev_group, name="lint")
def lint() -> int:
    """Run linters on the codebase."""

    from tux.cli.impl.dev import lint as run_lint

    return run_lint()


@command_registration_decorator(dev_group, name="lint-fix")
def lint_fix() -> int:
    """Run linters and apply fixes."""

    from tux.cli.impl.dev import lint_fix as run_lint_fix

    return run_lint_fix()


@command_registration_decorator(dev_group, name="format")
def format_code() -> int:
    """Run code formatters."""

    from tux.cli.impl.dev import format_code as run_format

    return run_format()


@command_registration_decorator(dev_group, name="typecheck")
def typecheck() -> int:
    """Check types with pyright."""

    from tux.cli.impl.dev import typecheck as run_typecheck

    return run_typecheck()


@command_registration_decorator(dev_group, name="check")
def check() -> int:
    """Run all checks (lint, format, typecheck)."""

    from tux.cli.impl.dev import check as run_check

    return run_check()
