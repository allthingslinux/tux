# ruff: noqa: T201

"""Command-line interface for Tux development tools."""

import os
import sys
from typing import NoReturn


# Set environment variables before importing any app modules
def set_environment(dev_mode: bool = False) -> None:
    """Set environment variables before importing any app modules."""
    os.environ["DEV"] = str(dev_mode).lower()


# Only import app modules after environment is set
def import_commands():
    """Import commands after environment is set."""
    from tux.main import run
    from tux.scripts import (
        check,
        db_generate,
        db_migrate,
        db_pull,
        db_push,
        db_reset,
        docs,
        docs_build,
        format_code,
        lint,
        lint_fix,
        typecheck,
    )

    return {
        # Bot commands
        "start": lambda: run(),
        "dev": lambda: run(),
        # Development tools
        "lint": lint,
        "lint-fix": lint_fix,
        "format": format_code,
        "typecheck": typecheck,
        "check": check,
        # Documentation
        "docs": docs,
        "docs-build": docs_build,
        # Database
        "db-generate": db_generate,
        "db-push": db_push,
        "db-pull": db_pull,
        "db-migrate": db_migrate,
        "db-reset": db_reset,
    }


def main() -> NoReturn:
    """Main entry point for the Tux CLI."""
    if len(sys.argv) < 2:
        print("Usage: poetry run tux <command>")
        print("\nAvailable commands:")

        categories = {
            "Bot": ["start", "dev"],
            "Development": ["lint", "lint-fix", "format", "typecheck", "check"],
            "Documentation": ["docs", "docs-build"],
            "Database": ["db-generate", "db-push", "db-pull", "db-migrate", "db-reset"],
        }

        for category, cmds in categories.items():
            print(f"\n{category}:")
            for cmd in cmds:
                print(f"  {cmd}")

        sys.exit(1)

    cmd = sys.argv[1]

    # Set environment before importing any app code
    set_environment(dev_mode=(cmd == "dev"))

    # Now import commands
    commands = import_commands()

    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

    sys.exit(commands[cmd]())
