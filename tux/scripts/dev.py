"""Development tools and utilities for Tux."""

from tux.scripts.core import run_command


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
