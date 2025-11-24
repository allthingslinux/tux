"""Configuration management CLI for Tux.

This script provides commands for generating and validating configuration files
in multiple formats using pydantic-settings-export CLI with proper config file handling.
"""

import subprocess
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scripts.base import BaseCLI
from tux.shared.config.settings import Config

app = typer.Typer(
    name="config",
    help="Configuration management and generation",
    no_args_is_help=True,
)

console = Console()


class ConfigCLI(BaseCLI):
    """Configuration management CLI."""

    def __init__(self) -> None:
        """Initialize the ConfigCLI."""
        super().__init__()


@app.command()
def generate(
    format_: Literal["env", "toml", "yaml", "json", "markdown", "all"] = typer.Option(  # type: ignore[assignment]
        "all",
        "--format",
        "-f",
        help="Format to generate (env, toml, yaml, json, markdown, all)",
    ),
    output: Path | None = typer.Option(  # type: ignore[assignment]  # noqa: B008
        None,
        "--output",
        "-o",
        help="Output file path (not supported with CLI approach - uses pyproject.toml paths)",
    ),
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
    console.print(Panel.fit("🔧 Configuration Generator", style="bold blue"))

    if output is not None:
        console.print(
            "✗ Custom output paths are not supported when using CLI approach",
            style="red",
        )
        console.print(
            "  Use pyproject.toml configuration to specify custom paths",
            style="yellow",
        )
        raise typer.Exit(code=1)

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        console.print("✗ pyproject.toml not found in current directory", style="red")
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
    format_map = {
        "env": ["dotenv"],
        "markdown": ["markdown"],
        "toml": ["tux.shared.config.generators:TomlGenerator"],
        "yaml": ["tux.shared.config.generators:YamlGenerator"],
        "json": ["tux.shared.config.generators:JsonGenerator"],
        "all": [
            "dotenv",
            "markdown",
            "tux.shared.config.generators:TomlGenerator",
            "tux.shared.config.generators:YamlGenerator",
            "tux.shared.config.generators:JsonGenerator",
        ],
    }

    formats_to_generate = format_map.get(format_, [])

    # Generate each format
    for generator in formats_to_generate:
        console.print(f"✓ Running generator: {generator}", style="green")

        cmd = [*base_cmd, "--generator", generator]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                console.print(f"  Output: {result.stdout.strip()}", style="dim")
        except subprocess.CalledProcessError as e:
            console.print(f"✗ Error running {generator}: {e}", style="red")
            if e.stdout:
                console.print(f"  Stdout: {e.stdout}", style="dim")
            if e.stderr:
                console.print(f"  Stderr: {e.stderr}", style="red")
            raise typer.Exit(code=1) from e

    console.print(
        "\n✅ Configuration files generated successfully!",
        style="bold green",
    )


@app.command()
def validate() -> None:
    """Validate the current configuration.

    This command loads the configuration from all sources and reports any issues,
    including missing required fields, invalid values, or file loading errors.

    Raises
    ------
    Exit
        If configuration validation fails.
    """
    console.print(Panel.fit("🔍 Configuration Validator", style="bold blue"))

    try:
        # Try to load the config
        config = Config()

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

        console.print(table)

        # Check for config files
        console.print("\n[bold]Configuration Files:[/bold]")
        for file_path in ["config.toml", "config.yaml", "config.json", ".env"]:
            path = Path(file_path)
            if path.exists():
                console.print(f"  ✓ {file_path} found", style="green")
            else:
                console.print(
                    f"  ○ {file_path} not found (using defaults)",
                    style="dim",
                )

        # Also check config/ directory for example files
        console.print("\n[bold]Example Files:[/bold]")
        config_dir = Path("config")
        if config_dir.exists():
            if example_files := list(config_dir.glob("*.example")):
                for example_file in sorted(example_files):
                    console.print(f"✓ {example_file} available", style="green")
            else:
                console.print(
                    f"✗ No example files in {config_dir}/ (run 'config generate')",
                    style="red",
                )

        console.print("\n✅ Configuration is valid!", style="bold green")

    except Exception as e:
        console.print(f"\n✗ Configuration validation failed: {e}", style="bold red")
        raise typer.Exit(code=1) from e


@app.command()
def show() -> None:
    """Show current configuration with sources.

    Displays the current configuration values and indicates which source
    each value came from (env var, file, or default).

    Raises
    ------
    Exit
        If configuration cannot be loaded.
    """
    console.print(Panel.fit("📋 Current Configuration", style="bold blue"))

    try:
        config = Config()

        # Create detailed table
        table = Table(
            show_header=True,
            header_style="bold magenta",
            title="All Configuration Settings",
        )
        table.add_column("Category", style="cyan")
        table.add_column("Setting", style="yellow")
        table.add_column("Value", style="green")

        # Core settings
        table.add_row("Core", "DEBUG", str(config.DEBUG))
        table.add_row("Core", "BOT_TOKEN", "***" if config.BOT_TOKEN else "NOT SET")

        # Database settings
        table.add_row("Database", "POSTGRES_HOST", config.POSTGRES_HOST)
        table.add_row("Database", "POSTGRES_PORT", str(config.POSTGRES_PORT))
        table.add_row("Database", "POSTGRES_DB", config.POSTGRES_DB)
        table.add_row("Database", "POSTGRES_USER", config.POSTGRES_USER)
        table.add_row(
            "Database",
            "POSTGRES_PASSWORD",
            "***" if config.POSTGRES_PASSWORD else "NOT SET",
        )

        # Bot info
        table.add_row("Bot Info", "BOT_NAME", config.BOT_INFO.BOT_NAME)
        table.add_row("Bot Info", "PREFIX", config.BOT_INFO.PREFIX)
        table.add_row("Bot Info", "HIDE_BOT_OWNER", str(config.BOT_INFO.HIDE_BOT_OWNER))

        # User IDs
        table.add_row("Users", "BOT_OWNER_ID", str(config.USER_IDS.BOT_OWNER_ID))
        table.add_row(
            "Users",
            "SYSADMINS",
            f"{len(config.USER_IDS.SYSADMINS)} configured",
        )

        console.print(table)

    except Exception as e:
        console.print(f"\n✗ Error loading configuration: {e}", style="bold red")
        raise typer.Exit(code=1) from e


def main() -> None:
    """Run the config CLI application."""
    app()


if __name__ == "__main__":
    main()
