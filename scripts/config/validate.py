"""
Command: config validate.

Validates configuration files.
"""

from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from typer import Exit

from scripts.core import create_app
from scripts.ui import console, create_progress_bar
from tux.shared.config.settings import Config

app = create_app()


@app.command(name="validate")
def validate() -> None:
    """Validate the current configuration."""
    console.print(Panel.fit("Configuration Validator", style="bold blue"))

    try:
        with create_progress_bar("Validating configuration...") as progress:
            progress.add_task("Loading settings...", total=None)
            config = Config()  # pyright: ignore[reportCallIssue]

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
        table.add_row("Database URL", f"{config.database_url[:50]}...", "✓")
        table.add_row("Bot Name", config.BOT_INFO.BOT_NAME, "✓")
        table.add_row("Prefix", config.BOT_INFO.PREFIX, "✓")

        console.print(table)

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
