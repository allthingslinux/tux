# ruff: noqa: T201

"""Command-line interface for Tux development tools."""

import os
import sys
from collections.abc import Callable
from typing import NoReturn, TypeVar

T = TypeVar("T")

# Define command types
CommandFunction = Callable[[], int]
CommandDict = dict[str, "CommandFunction"]
Command = CommandFunction | CommandDict


# Set environment variables before importing any app modules
def set_environment(dev_mode: bool = True) -> None:
    """Set environment variables before importing any app modules."""
    os.environ["DEV"] = str(dev_mode).lower()


# Only import app modules after environment is set
def import_commands() -> dict[str, Command]:
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

    # Database command factory
    def create_db_command(cmd_func: CommandFunction, default_dev: bool = True) -> CommandFunction:
        """
        Create a database command function that handles environment flags.

        Parameters
        ----------
        cmd_func : CommandFunction
            The database command function
        default_dev : bool
            Whether to use development mode by default

        Returns
        -------
        CommandFunction
            The wrapped command function
        """

        def db_cmd() -> int:
            # Check if --prod or --dev flag is present
            args = sys.argv[2:] if len(sys.argv) > 2 else []

            if "--prod" in args:
                return run_with_env(False, cmd_func)
            if "--dev" in args:
                return run_with_env(True, cmd_func)
            return run_with_env(default_dev, cmd_func)

        return db_cmd

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
        # Database commands (with environment flag support)
        "db": {
            "generate": create_db_command(db_generate),
            "push": create_db_command(db_push),
            "pull": create_db_command(db_pull),
            "migrate": create_db_command(db_migrate),
            "reset": create_db_command(db_reset),
        },
    }


def run_with_env(dev_mode: bool, func: Callable[[], T]) -> T:
    """
    Run a function with a specific environment setting.

    Parameters
    ----------
    dev_mode : bool
        Whether to run in development mode
    func : Callable[[], T]
        The function to run

    Returns
    -------
    T
        The return value of the function
    """
    # Save current environment setting
    original_dev = os.environ.get("DEV", "true").lower() == "true"

    # Set new environment
    set_environment(dev_mode)

    try:
        # Run the function
        return func()
    finally:
        # Restore original environment
        set_environment(original_dev)


def main() -> NoReturn:
    """Main entry point for the Tux CLI."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1]

    # Handle nested commands (e.g., "db:generate")
    if ":" in cmd:
        namespace, subcommand = cmd.split(":", 1)
        sys.argv[1] = namespace  # Replace with namespace for correct arg processing later
        return handle_namespaced_command(namespace, subcommand)

    # Set environment before importing any app code
    # For standard commands
    set_environment(dev_mode=(cmd == "dev"))

    # Now import commands
    commands = import_commands()

    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

    # Handle nested command groups
    if cmd == "db" and len(sys.argv) > 2:
        command_group = commands["db"]
        if isinstance(command_group, dict):
            return handle_db_command(command_group)
        print(f"'{cmd}' is not a command group.")
        sys.exit(1)

    # Handle direct commands
    command = commands[cmd]
    if isinstance(command, dict):
        print(f"'{cmd}' is a command group. Use '{cmd}:subcommand' syntax.")
        print(f"Available subcommands: {', '.join(command.keys())}")
        sys.exit(1)

    # Execute function command
    sys.exit(command())


def handle_namespaced_command(namespace: str, subcommand: str) -> NoReturn:
    """Handle a namespaced command like 'db:generate'."""
    commands = import_commands()

    if namespace not in commands:
        print(f"Unknown command namespace: {namespace}")
        sys.exit(1)

    command = commands[namespace]
    if not isinstance(command, dict):
        print(f"'{namespace}' is not a command group.")
        sys.exit(1)

    command_dict = command  # Type is now narrowed to dict
    if subcommand not in command_dict:
        print(f"Unknown subcommand: {namespace}:{subcommand}")
        print(f"Available subcommands: {', '.join(command_dict.keys())}")
        sys.exit(1)

    sys.exit(command_dict[subcommand]())


def handle_db_command(db_commands: CommandDict) -> NoReturn:
    """Handle a database command."""
    subcommand = sys.argv[2]

    if subcommand not in db_commands:
        print(f"Unknown database command: {subcommand}")
        print(f"Available commands: {', '.join(db_commands.keys())}")
        sys.exit(1)

    sys.exit(db_commands[subcommand]())


def print_help() -> None:
    """Print CLI help information."""
    print("Usage: poetry run tux <command>")
    print("\nAvailable commands:")

    categories = {
        "Bot": ["start", "dev"],
        "Development": ["lint", "lint-fix", "format", "typecheck", "check"],
        "Documentation": ["docs", "docs-build"],
        "Database": [
            "db:generate",
            "db:push",
            "db:pull",
            "db:migrate",
            "db:reset",
        ],
    }

    for category, cmds in categories.items():
        print(f"\n{category}:")
        for cmd in cmds:
            print(f"  {cmd}")

    print("\nDatabase Environment Flags:")
    print("  Add --dev or --prod to specify environment:")
    print("  Example: poetry run tux db:generate --prod")
