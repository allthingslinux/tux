"""
Command: config validate.

Validates configuration files.
"""

from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from typer import Exit

from scripts.core import create_app
from scripts.ui import console, create_status
from tux.shared.config.settings import Config

app = create_app()

# Constants
DB_URL_DISPLAY_LENGTH = 50


@app.command(name="validate")
def validate() -> None:
    """Validate the current configuration."""
    console.print(Panel.fit("Configuration Validator", style="bold blue"))

    try:
        with create_status("Validating configuration...") as status:
            config = Config()  # pyright: ignore[reportCallIssue]
            status.update("[bold green]Validation complete![/bold green]")

        table = Table(
            title="Configuration Summary",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")

        table.add_row("DEBUG", str(config.DEBUG), "✓")
        table.add_row(
            "BOT_TOKEN",
            "***" if config.BOT_TOKEN else "NOT SET",
            "✓" if config.BOT_TOKEN else "✗",
        )
        db_url = config.database_url
        db_url_display = (
            f"{db_url[:DB_URL_DISPLAY_LENGTH]}..."
            if len(db_url) > DB_URL_DISPLAY_LENGTH
            else db_url
        )
        table.add_row("Database URL", db_url_display, "✓")
        table.add_row("Bot Name", config.BOT_INFO.BOT_NAME, "✓")
        table.add_row("Prefix", config.BOT_INFO.PREFIX, "✓")

        console.print(table)

        console.print("\n[bold]Configuration Files:[/bold]")
        for file_path in [
            "config/config.toml",
            "config/config.yaml",
            "config/config.json",
            ".env",
        ]:
            path = Path(file_path)
            if path.exists():
                console.print(f"  ✓ {file_path} found", style="green")
            else:
                console.print(
                    f"  ○ {file_path} not found (using defaults)",
                    style="dim",
                )

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

        console.print("\nConfiguration is valid!", style="bold green")

    except Exception as e:
        console.print(f"\nConfiguration validation failed: {e}", style="bold red")
        raise Exit(code=1) from e


if __name__ == "__main__":
    app()
