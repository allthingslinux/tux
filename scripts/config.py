"""Configuration management CLI for Tux.

This script provides commands for generating and validating configuration files
in multiple formats using pydantic-settings-export and custom generators.
"""

import warnings
from pathlib import Path
from typing import Literal

import typer
from pydantic_settings_export import Exporter, PSESettings
from pydantic_settings_export.generators.dotenv import DotEnvGenerator, DotEnvSettings
from pydantic_settings_export.generators.markdown import MarkdownGenerator, MarkdownSettings
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scripts.base import BaseCLI
from tux.shared.config.generators import (
    JsonGenerator,
    TomlGenerator,
    YamlGenerator,
)
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
        help="Output file path (only for single format)",
    ),
) -> None:
    """Generate configuration example files in various formats.

    This command uses pydantic-settings-export and custom generators to create
    example configuration files from your Pydantic settings model.

    Parameters
    ----------
    format : Literal["env", "toml", "yaml", "json", "markdown", "all"]
        The format(s) to generate
    output : Path | None
        Optional output file path (only used with single format)

    """
    console.print(Panel.fit("🔧 Configuration Generator", style="bold blue"))

    # Suppress warning about pyproject_toml_table_header from PSESettings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*pyproject_toml_table_header.*")
        pse_settings = PSESettings(root_dir=Path.cwd(), project_dir=Path.cwd(), respect_exclude=True)

    # Collect all generators
    generators = []

    # Add env generator
    if format_ in ("all", "env"):
        env_path = output if output and format_ == "env" else Path(".env.example")
        generators.append(DotEnvGenerator(pse_settings, DotEnvSettings(paths=[env_path])))  # type: ignore[arg-type]
        console.print(f"✓ .env generator configured: {env_path}", style="green")

    # Add markdown generator
    if format_ in ("all", "markdown"):
        md_path = output if output and format_ == "markdown" else Path("docs/content/reference/configuration.md")
        generators.append(MarkdownGenerator(pse_settings, MarkdownSettings(paths=[md_path])))  # type: ignore[arg-type]
        console.print(f"✓ Markdown generator configured: {md_path}", style="green")

    # Add custom format generators
    if format_ in ("all", "toml"):
        toml_path = output if output and format_ == "toml" else Path("config/config.toml.example")
        generators.append(TomlGenerator(pse_settings, TomlGenerator.config(paths=[toml_path], enabled=True)))  # type: ignore[arg-type]
        console.print(f"✓ TOML generator configured: {toml_path}", style="green")

    if format_ in ("all", "yaml"):
        yaml_path = output if output and format_ == "yaml" else Path("config/config.yaml.example")
        generators.append(YamlGenerator(pse_settings, YamlGenerator.config(paths=[yaml_path], enabled=True)))  # type: ignore[arg-type]
        console.print(f"✓ YAML generator configured: {yaml_path}", style="green")

    if format_ in ("all", "json"):
        json_path = output if output and format_ == "json" else Path("config/config.json.example")
        generators.append(JsonGenerator(pse_settings, JsonGenerator.config(paths=[json_path], enabled=True)))  # type: ignore[arg-type]
        console.print(f"✓ JSON generator configured: {json_path}", style="green")

    # Run all generators
    if generators:
        try:
            exporter = Exporter(pse_settings, generators=generators)
            exporter.run_all(Config)
            console.print("\n✅ Configuration files generated successfully!", style="bold green")
        except Exception as e:
            console.print(f"\n✗ Error generating config files: {e}", style="red")
            raise typer.Exit(code=1) from e
    else:
        console.print(f"✗ No valid format specified: {format_}", style="red")
        raise typer.Exit(code=1)


@app.command()
def validate() -> None:
    """Validate the current configuration.

    This command loads the configuration from all sources and reports any issues,
    including missing required fields, invalid values, or file loading errors.
    """
    console.print(Panel.fit("🔍 Configuration Validator", style="bold blue"))

    try:
        # Try to load the config
        config = Config()

        # Create a summary table
        table = Table(title="Configuration Summary", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")

        # Show some key settings
        table.add_row("DEBUG", str(config.DEBUG), "✓")
        table.add_row("BOT_TOKEN", "***" if config.BOT_TOKEN else "NOT SET", "✓" if config.BOT_TOKEN else "✗")
        table.add_row("Database URL", config.database_url[:50] + "...", "✓")
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
                console.print(f"  ○ {file_path} not found (using defaults)", style="dim")

        # Also check config/ directory for example files
        console.print("\n[bold]Example Files:[/bold]")
        config_dir = Path("config")
        if config_dir.exists():
            example_files = list(config_dir.glob("*.example"))
            if example_files:
                for example_file in sorted(example_files):
                    console.print(f"✓ {example_file} available", style="green")
            else:
                console.print(f"✗ No example files in {config_dir}/ (run 'config generate')", style="red")

        console.print("\n✅ Configuration is valid!", style="bold green")

    except Exception as e:
        console.print(f"\n✗ Configuration validation failed: {e}", style="bold red")
        raise typer.Exit(code=1) from e


@app.command()
def show() -> None:
    """Show current configuration with sources.

    Displays the current configuration values and indicates which source
    each value came from (env var, file, or default).
    """
    console.print(Panel.fit("📋 Current Configuration", style="bold blue"))

    try:
        config = Config()

        # Create detailed table
        table = Table(show_header=True, header_style="bold magenta", title="All Configuration Settings")
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
        table.add_row("Database", "POSTGRES_PASSWORD", "***" if config.POSTGRES_PASSWORD else "NOT SET")

        # Bot info
        table.add_row("Bot Info", "BOT_NAME", config.BOT_INFO.BOT_NAME)
        table.add_row("Bot Info", "PREFIX", config.BOT_INFO.PREFIX)
        table.add_row("Bot Info", "HIDE_BOT_OWNER", str(config.BOT_INFO.HIDE_BOT_OWNER))

        # User IDs
        table.add_row("Users", "BOT_OWNER_ID", str(config.USER_IDS.BOT_OWNER_ID))
        table.add_row("Users", "SYSADMINS", str(len(config.USER_IDS.SYSADMINS)) + " configured")

        console.print(table)

    except Exception as e:
        console.print(f"\n✗ Error loading configuration: {e}", style="bold red")
        raise typer.Exit(code=1) from e


def main() -> None:
    """Run the config CLI application."""
    app()


if __name__ == "__main__":
    main()
