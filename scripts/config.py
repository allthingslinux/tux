"""Configuration management CLI for Tux.

This script provides commands for generating and validating configuration files
in multiple formats using pydantic-settings-export CLI with proper config file handling.
"""

import subprocess
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.panel import Panel
from rich.table import Table
from typer import Option  # type: ignore[attr-defined]

from scripts.base import BaseCLI
from scripts.registry import Command

# Import custom generators to ensure they're registered before CLI runs
# These imports are needed for registration, even if not directly used
from tux.shared.config.generators import (
    JsonGenerator,  # noqa: F401 # pyright: ignore[reportUnusedImport]
    YamlGenerator,  # noqa: F401 # pyright: ignore[reportUnusedImport]
)
from tux.shared.config.settings import Config


class ConfigCLI(BaseCLI):
    """Configuration management CLI."""

    def __init__(self) -> None:
        """Initialize the ConfigCLI."""
        super().__init__(
            name="config",
            description="Configuration management and generation",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all configuration commands."""
        all_commands = [
            Command(
                "generate",
                self.generate,
                "Generate configuration example files in various formats",
            ),
            Command(
                "validate",
                self.validate,
                "Validate the current configuration",
            ),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Set up all configuration CLI commands using the command registry."""
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def generate(
        self,
        format_: Annotated[
            Literal["env", "toml", "yaml", "json", "markdown", "all"],
            Option(
                "--format",
                "-f",
                help="Format to generate (env, toml, yaml, json, markdown, all)",
            ),
        ] = "all",
        output: Annotated[
            Path | None,
            Option(
                "--output",
                "-o",
                help="Output file path (not supported with CLI approach - uses pyproject.toml paths)",
            ),
        ] = None,
    ) -> None:
        """Generate configuration example files in various formats.

        This command uses pydantic-settings-export CLI with the --config-file flag
        to ensure proper configuration loading from pyproject.toml.

        Parameters
        ----------
        format : Literal["env", "toml", "yaml", "json", "markdown", "all"]
            The format(s) to generate
        output : Path | None
            Not supported - output paths are configured in pyproject.toml

        Raises
        ------
        Exit
            If configuration generation fails.
        """
        self.console.print(Panel.fit("🔧 Configuration Generator", style="bold blue"))

        if output is not None:
            self.console.print(
                "✗ Custom output paths are not supported when using CLI approach",
                style="red",
            )
            self.console.print(
                "  Use pyproject.toml configuration to specify custom paths",
                style="yellow",
            )
            raise typer.Exit(code=1)

        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            self.console.print(
                "✗ pyproject.toml not found in current directory",
                style="red",
            )
            raise typer.Exit(code=1)

        # Build base command with config file
        base_cmd = [
            "uv",
            "run",
            "pydantic-settings-export",
            "--config-file",
            str(pyproject_path),
        ]

        # Map formats to generators
        # Generators are imported at module level to ensure registration
        # Use module paths for custom generators, names for built-in ones
        format_map = {
            "env": ["dotenv"],
            "markdown": ["markdown"],  # Built-in markdown generator
            "toml": ["toml"],  # Built-in TOML generator
            "yaml": [
                "tux.shared.config.generators:YamlGenerator",
            ],  # Custom YAML generator
            "json": [
                "tux.shared.config.generators:JsonGenerator",
            ],  # Custom JSON generator
            "all": [
                "dotenv",
                "markdown",  # Built-in markdown generator
                "toml",  # Built-in TOML generator
                "tux.shared.config.generators:YamlGenerator",  # Custom YAML generator
                "tux.shared.config.generators:JsonGenerator",  # Custom JSON generator
            ],
        }

        formats_to_generate = format_map.get(format_, [])

        # Generate each format
        for generator in formats_to_generate:
            self.console.print(f"✓ Running generator: {generator}", style="green")

            cmd = [*base_cmd, "--generator", generator]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                if result.stdout:
                    self.console.print(
                        f"  Output: {result.stdout.strip()}",
                        style="dim",
                    )
            except subprocess.CalledProcessError as e:
                self.console.print(f"✗ Error running {generator}: {e}", style="red")
                if e.stdout:
                    self.console.print(f"  Stdout: {e.stdout}", style="dim")
                if e.stderr:
                    self.console.print(f"  Stderr: {e.stderr}", style="red")
                raise typer.Exit(code=1) from e

        self.console.print(
            "\n✅ Configuration files generated successfully!",
            style="bold green",
        )

    def validate(self) -> None:
        """Validate the current configuration.

        This command loads the configuration from all sources and reports any issues,
        including missing required fields, invalid values, or file loading errors.

        Raises
        ------
        Exit
            If configuration validation fails.
        """
        self.console.print(Panel.fit("🔍 Configuration Validator", style="bold blue"))

        try:
            # Try to load the config
            config = Config()  # pyright: ignore[reportCallIssue]

            # Create a summary table
            table = Table(
                title="Configuration Summary",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Setting", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")
            table.add_column("Source", style="yellow")

            # Show some key settings
            table.add_row("DEBUG", str(config.DEBUG), "✓")
            table.add_row(
                "BOT_TOKEN",
                "***" if config.BOT_TOKEN else "NOT SET",
                "✓" if config.BOT_TOKEN else "✗",
            )
            table.add_row("Database URL", f"{config.database_url[:50]}...", "✓")
            table.add_row("Bot Name", config.BOT_INFO.BOT_NAME, "✓")
            table.add_row("Prefix", config.BOT_INFO.PREFIX, "✓")

            self.console.print(table)

            # Check for config files
            self.console.print("\n[bold]Configuration Files:[/bold]")
            for file_path in ["config.toml", "config.yaml", "config.json", ".env"]:
                path = Path(file_path)
                if path.exists():
                    self.console.print(f"  ✓ {file_path} found", style="green")
                else:
                    self.console.print(
                        f"  ○ {file_path} not found (using defaults)",
                        style="dim",
                    )

            # Also check config/ directory for example files
            self.console.print("\n[bold]Example Files:[/bold]")
            config_dir = Path("config")
            if config_dir.exists():
                if example_files := list(config_dir.glob("*.example")):
                    for example_file in sorted(example_files):
                        self.console.print(f"✓ {example_file} available", style="green")
                else:
                    self.console.print(
                        f"✗ No example files in {config_dir}/ (run 'config generate')",
                        style="red",
                    )

            self.console.print("\n✅ Configuration is valid!", style="bold green")

        except Exception as e:
            self.console.print(
                f"\n✗ Configuration validation failed: {e}",
                style="bold red",
            )
            raise typer.Exit(code=1) from e


# Create the CLI app instance for mkdocs-typer
app = ConfigCLI().app


def main() -> None:
    """Entry point for the configuration CLI script."""
    cli = ConfigCLI()
    cli.run()


if __name__ == "__main__":
    main()
