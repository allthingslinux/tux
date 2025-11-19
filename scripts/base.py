"""
Base CLI Infrastructure.

Provides the base CLI class that all CLI applications should inherit from.
"""

import os
import subprocess
from collections.abc import Callable

from dotenv import load_dotenv  # type: ignore[import-untyped]
from rich.console import Console
from typer import Typer

from scripts.registry import CommandRegistry
from scripts.rich_utils import RichCLI
from tux.core.logging import configure_logging

# Load .env file to make environment variables available to subprocesses
# This ensures env vars are available when running commands via uv run, etc.
load_dotenv()


class BaseCLI:
    """Base class for all CLI applications.

    Provides the foundation for CLI applications with Rich console support,
    command registry integration, and common CLI utilities.

    Parameters
    ----------
    name : str, optional
        The name of the CLI application (default is "cli").
    description : str, optional
        Description of the CLI application (default is "CLI Application").

    Attributes
    ----------
    app : Typer
        The main Typer application instance.
    console : Console
        Rich console for output formatting.
    rich : RichCLI
        Rich CLI utilities for enhanced output.
    _command_registry : CommandRegistry
        Registry for managing CLI commands.
    """

    app: Typer
    console: Console
    rich: RichCLI
    _command_registry: CommandRegistry

    def __init__(self, name: str = "cli", description: str = "CLI Application"):
        """Initialize the base CLI application.

        Sets up the Typer app, console, rich utilities, and command registry.
        Subclasses should override _setup_commands() to add their specific commands.

        Parameters
        ----------
        name : str, optional
            The name of the CLI application (default is "cli").
        description : str, optional
            Description of the CLI application (default is "CLI Application").
        """
        self.app = Typer(
            name=name,
            help=description,
            rich_markup_mode="rich",
            no_args_is_help=True,
        )
        self.console = Console()
        self.rich = RichCLI()
        self._command_registry = CommandRegistry()
        self._setup_commands()

    def _setup_commands(self) -> None:
        """Set up commands for the CLI application.

        This method should be overridden by subclasses to add their specific
        commands to the CLI application. The base implementation does nothing.
        """

    def create_subcommand_group(self, name: str, help_text: str, rich_help_panel: str | None = None) -> Typer:
        """Create a new subcommand group.

        Creates a Typer application instance configured for use as a subcommand
        group with Rich markup support.

        Parameters
        ----------
        name : str
            The name of the subcommand group.
        help_text : str
            Help text describing the subcommand group.
        rich_help_panel : str, optional
            Rich help panel name for grouping commands in help output.

        Returns
        -------
        Typer
            A configured Typer application instance for the subcommand group.
        """
        return Typer(
            name=name,
            help=help_text,
            rich_markup_mode="rich",
            no_args_is_help=True,
        )

    def add_command(
        self,
        func: Callable[..., None],
        name: str | None = None,
        help_text: str | None = None,
        sub_app: Typer | None = None,
    ) -> None:
        """Add a command to the CLI application.

        Registers a function as a CLI command with the specified Typer application.

        Parameters
        ----------
        func : Callable[..., None]
            The function to register as a command.
        name : str, optional
            Custom name for the command. If None, uses the function name.
        help_text : str, optional
            Help text for the command. If None, uses command registry help text.
        sub_app : Typer, optional
            The Typer app to add the command to. If None, uses the main app.
        """
        target_app = sub_app or self.app
        # Always use help_text from command registry as single source of truth
        target_app.command(name=name, help=help_text)(func)

    def add_subcommand_group(self, sub_app: Typer, name: str, rich_help_panel: str | None = None) -> None:
        """Add a subcommand group to the main application.

        Registers a Typer subcommand group with the main CLI application.

        Parameters
        ----------
        sub_app : Typer
            The Typer application to add as a subcommand group.
        name : str
            The name of the subcommand group.
        rich_help_panel : str, optional
            Rich help panel name for grouping commands in help output.
        """
        self.app.add_typer(sub_app, name=name, rich_help_panel=rich_help_panel)

    def _run_command(self, command: list[str]) -> None:
        """Run a shell command and handle output.

        Executes a shell command using subprocess and handles stdout/stderr output.
        Explicitly passes environment variables to ensure they're available to
        subprocesses, especially when using uv run or other tools that may not
        inherit all environment variables.

        Parameters
        ----------
        command : list[str]
            The command and arguments to execute.

        Raises
        ------
        subprocess.CalledProcessError
            If the command returns a non-zero exit code.
        """
        try:
            # Explicitly pass environment variables to ensure they're available
            # This is especially important for uv run which may not inherit all env vars
            result = subprocess.run(command, check=True, capture_output=True, text=True, env=os.environ.copy())
            if result.stdout:
                self.console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            self.rich.print_error(f"Command failed: {' '.join(command)}")
            if e.stderr:
                self.console.print(f"[red]{e.stderr}[/red]")
            raise

    def run(self) -> None:
        """Run the CLI application with automatic logging configuration.

        Configures logging and starts the Typer application. This is the main
        entry point for running the CLI.
        """
        # Load CONFIG to respect DEBUG setting from .env
        from tux.shared.config import CONFIG  # noqa: PLC0415

        configure_logging(config=CONFIG)
        self.app()
