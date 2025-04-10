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

from tux.cli.ui import command_header, command_result, error, info, warning
from tux.utils.env import (
    configure_environment,
    get_current_env,
    get_database_url,
)
from tux.utils.logger import setup_logging

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


# Initialize interface CLI group
@click.group()
@click.version_option(prog_name="Tux")
@click.option("--dev", "env_dev", is_flag=True, help="Run in development mode (default)")
@click.option("--prod", "env_prod", is_flag=True, help="Run in production mode")
@click.pass_context
def cli(ctx: Context, env_dev: bool, env_prod: bool) -> None:
    """Tux CLI"""

    # Initialize context object
    ctx.ensure_object(dict)

    # Determine and configure the environment mode.
    # Production mode (--prod) takes precedence over development (--dev).
    # Defaults to development if neither flag is provided.
    is_dev = not env_prod  # True if --prod is NOT set
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

    modules = ["bot", "database", "dev", "docs", "docker"]

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
