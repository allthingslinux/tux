"""Core CLI functionality for Tux.

This module provides the main Click command group and utilities for the CLI.
"""

import importlib
import os
import subprocess
import sys
from collections.abc import Callable
from functools import update_wrapper
from typing import Any, TypeVar

import click
from click import Command, Context, Group
from loguru import logger

# Import version from main package
from tux import __version__
from utils.env import (
    configure_environment,
    get_current_env,
    get_database_url,
)
from utils.logger import setup_logging

from cli.ui import command_header, command_result, error, info, warning

# Type definitions
T = TypeVar("T")
CommandFunction = Callable[..., int]

# Help text suffix for groups
GROUP_HELP_SUFFIX = ""

# Commands/groups that do not require database access
NO_DB_COMMANDS = {"dev", "docs", "docker"}


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


# Custom Group to handle global options (--dev/--prod) regardless of position
class GlobalOptionGroup(click.Group):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        """
        Parses arguments, extracting global --dev/--prod flags first.

        Stores the determined environment mode in ctx.meta['is_dev'].
        Removes the flags from the args list before standard parsing.
        """
        is_dev = True  # Default to development mode
        remaining_args: list[str] = []
        args_iterator = iter(args)

        for arg in args_iterator:
            if arg == "--dev":
                is_dev = True  # Explicitly set, though already default
            elif arg == "--prod":
                is_dev = False
            else:
                remaining_args.append(arg)

        # Store the determined mode in the context metadata
        ctx.meta["is_dev"] = is_dev

        # Call the default parser with the modified arguments
        return super().parse_args(ctx, remaining_args)

    # Override group help to show global options if needed, although Click
    # might handle version_option separately. Keeping this simple for now.


# Initialize interface CLI group using the custom class
@click.group(cls=GlobalOptionGroup)
@click.version_option(version=__version__, prog_name="Tux")  # type: ignore[misc]
@click.pass_context
def cli(ctx: Context) -> None:  # Remove env_dev and env_prod params
    """Tux CLI"""

    # Initialize context object
    ctx.ensure_object(dict)  # Still useful for subcommands if they use ctx.obj
    ctx.meta.setdefault("is_dev", True)  # Ensure 'is_dev' exists even if parse_args wasn't fully run (e.g., --help)

    # Retrieve the environment mode set by GlobalOptionGroup.parse_args
    is_dev = ctx.meta["is_dev"]
    configure_environment(dev_mode=is_dev)

    # Conditionally set DATABASE_URL for commands that require it
    invoked_command = ctx.invoked_subcommand

    if invoked_command is not None and invoked_command not in NO_DB_COMMANDS:
        logger.trace(f"Command '{invoked_command}' may require database access. Setting DATABASE_URL.")
        try:
            db_url = get_database_url()
            os.environ["DATABASE_URL"] = db_url
            logger.trace("Set DATABASE_URL environment variable for Prisma.")
        except Exception as e:
            # Log critical error and exit if URL couldn't be determined for a required command.
            logger.critical(f"Command '{invoked_command}' requires a database, but failed to configure URL: {e}")
            logger.critical("Ensure DEV_DATABASE_URL or PROD_DATABASE_URL is set in your .env file or environment.")
            sys.exit(1)  # Exit with a non-zero status code
    elif invoked_command:
        logger.trace(f"Command '{invoked_command}' does not require database access. Skipping DATABASE_URL setup.")
    # else: invoked_command is None (e.g., `tux --help`), no DB needed.


def command_registration_decorator(
    target_group: Group,
    *args: Any,
    **kwargs: Any,
) -> Callable[[CommandFunction], Command]:
    """
    Universal command decorator for registering commands on any group.

    Handles UI output and error handling.
    Environment is configured globally.
    Extracts params for the original function from ctx.params.
    """

    def decorator(func: CommandFunction) -> Command:
        # Define the wrapper that will be registered as the command
        # Remove dev/prod options here
        @click.pass_context
        def wrapper(ctx: Context, **kwargs: Any):
            # This wrapper receives ctx and all original func params via kwargs
            # Environment is assumed to be set by the global cli options.

            # Get group and command names for output using context, ensuring non-None
            group_name = (ctx.parent.command.name or "cli") if ctx.parent and ctx.parent.command else "cli"
            cmd_name = (ctx.command.name or "unknown") if ctx.command else "unknown"

            # Echo environment mode and command info
            command_header(group_name, cmd_name)

            # Display env info unconditionally now, as it's globally set
            info(f"Running in {get_current_env()} mode")

            # Execute the original command function
            try:
                # Pass all kwargs received directly to the original function
                result = func(**kwargs)
                success = result == 0
                command_result(success)
                # Return the actual result from the function
                return result  # noqa: TRY300

            except Exception as e:
                error(f"Command failed: {e!s}")
                logger.exception("An error occurred during command execution.")
                command_result(False)
                return 1

        # Update wrapper metadata from original function
        wrapper = update_wrapper(wrapper, func)

        # Register the wrapper function with the target group
        return target_group.command(*args, **kwargs)(wrapper)

    return decorator


def create_group(name: str, help_text: str) -> Group:
    """Create a new command group and register it with the main CLI."""

    # No need to append suffix anymore
    @cli.group(name=name, help=help_text)
    def group_func() -> None:
        pass

    # Return the group created by the decorator
    return group_func


def register_commands() -> None:
    """Load and register all CLI commands."""

    modules = ["database", "dev", "docs", "docker", "test"]

    for module_name in modules:
        try:
            importlib.import_module(f"tux.cli.{module_name}")

        except ImportError as e:
            warning(f"Failed to load command module {module_name}: {e}")


def main() -> int:
    """Entry point for the CLI."""

    # Configure logging first!
    setup_logging()

    # No need for default env config here, handled by @cli options
    # register_commands()

    # Run the CLI
    # Click will parse global options, call cli func, then subcommand func
    # We need to ensure commands are registered before cli() is called.
    register_commands()
    return cli() or 0  # Return 0 if cli() returns None


# Register the start command directly under the main cli group
@command_registration_decorator(cli, name="start")
def start() -> int:
    """Start the Discord bot"""

    from main import run  # noqa: PLC0415

    result = run()
    return 0 if result is None else result


# Register the version command directly under the main cli group
@command_registration_decorator(cli, name="version")
def show_version() -> int:
    """Display the current version of Tux"""

    info(f"Tux version: {__version__}")
    return 0


# Ensure commands are registered when this module is imported
register_commands()
