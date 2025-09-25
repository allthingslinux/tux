#!/usr/bin/env python3

"""
Tux Bot CLI Script

A unified interface for all Tux bot operations using the clean CLI infrastructure.
"""

import sys
from pathlib import Path
from typing import Annotated

from typer import Option  # type: ignore[attr-defined]

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.base import BaseCLI
from scripts.registry import Command


class TuxCLI(BaseCLI):
    """Tux Bot CLI with unified interface for all bot operations."""

    def __init__(self):
        super().__init__(name="tux", description="Tux Bot CLI - A unified interface for all bot operations")
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Setup the command registry with all Tux bot commands."""
        # All commands directly registered without groups
        all_commands = [
            # Bot operations
            Command("start", self.start_bot, "Start the Tux Discord bot"),
            Command("version", self.show_version, "Show Tux version information"),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Setup all Tux CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    # ========================================================================
    # BOT COMMANDS
    # ========================================================================

    def start_bot(
        self,
        debug: Annotated[bool, Option("--debug", help="Enable debug mode")] = False,
    ) -> None:
        """Start the Tux Discord bot.

        This command starts the main Tux Discord bot with all its features.
        Use --debug to enable debug mode for development.
        """
        self.rich.print_section("🚀 Starting Tux Bot", "blue")
        self.rich.rich_print("[bold blue]Starting Tux Discord bot...[/bold blue]")

        try:
            # Import here to avoid circular imports
            from tux.main import run  # noqa: PLC0415

            if debug:
                self.rich.print_info("🐛 Debug mode enabled")

            exit_code = run()
            if exit_code == 0:
                self.rich.print_success("✅ Bot started successfully")
            else:
                self.rich.print_error(f"❌ Bot exited with code {exit_code}")
                sys.exit(exit_code)

        except RuntimeError as e:
            # Handle setup failures (database, container, etc.)
            if "setup failed" in str(e).lower():
                # Error already logged in setup method, just exit
                self.rich.print_error("❌ Bot setup failed")
                sys.exit(1)
            elif "Event loop stopped before Future completed" in str(e):
                self.rich.print_info("🛑 Bot shutdown completed")
                sys.exit(0)
            else:
                self.rich.print_error(f"❌ Runtime error: {e}")
                sys.exit(1)
        except SystemExit as e:
            # Bot failed during startup, exit with the proper code
            # Don't log additional error messages since they're already handled
            sys.exit(e.code)
        except KeyboardInterrupt:
            self.rich.print_info("🛑 Bot shutdown requested by user (Ctrl+C)")
            sys.exit(0)
        except Exception as e:
            self.rich.print_error(f"❌ Failed to start bot: {e}")
            sys.exit(1)

    def show_version(self) -> None:
        """Show Tux version information.

        Displays the current version of Tux and related components.
        """
        self.rich.print_section("📋 Tux Version Information", "blue")
        self.rich.rich_print("[bold blue]Showing Tux version information...[/bold blue]")

        try:
            from tux import __version__  # noqa: PLC0415

            self.rich.rich_print(f"[green]Tux version: {__version__}[/green]")
            self.rich.print_success("Version information displayed")

        except ImportError as e:
            self.rich.print_error(f"Failed to import version: {e}")
            sys.exit(1)
        except Exception as e:
            self.rich.print_error(f"Failed to show version: {e}")
            sys.exit(1)


# Create the CLI app instance for mkdocs-typer
app = TuxCLI().app


def main() -> None:
    """Entry point for the Tux CLI script."""
    cli = TuxCLI()
    cli.run()


if __name__ == "__main__":
    main()
