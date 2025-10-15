"""
Base CLI Infrastructure.

Provides the base CLI class that all CLI applications should inherit from.
"""

import subprocess
from collections.abc import Callable

from rich.console import Console
from typer import Typer

from scripts.registry import CommandRegistry
from scripts.rich_utils import RichCLI
from tux.core.logging import configure_logging


class BaseCLI:
    """Base class for all CLI applications."""

    app: Typer
    console: Console
    rich: RichCLI
    _command_registry: CommandRegistry

    def __init__(self, name: str = "cli", description: str = "CLI Application"):
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
        """Set up commands - to be overridden by subclasses."""

    def create_subcommand_group(self, name: str, help_text: str, rich_help_panel: str | None = None) -> Typer:
        """Create a subcommand group."""
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
        """Add a command to the CLI."""
        target_app = sub_app or self.app
        # Always use help_text from command registry as single source of truth
        target_app.command(name=name, help=help_text)(func)

    def add_subcommand_group(self, sub_app: Typer, name: str, rich_help_panel: str | None = None) -> None:
        """Add a subcommand group to the main app."""
        self.app.add_typer(sub_app, name=name, rich_help_panel=rich_help_panel)

    def _run_command(self, command: list[str]) -> None:
        """Run a shell command."""
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if result.stdout:
                self.console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            self.rich.print_error(f"Command failed: {' '.join(command)}")
            if e.stderr:
                self.console.print(f"[red]{e.stderr}[/red]")
            raise

    def run(self) -> None:
        """Run the CLI application with automatic logging configuration."""
        configure_logging()
        self.app()
