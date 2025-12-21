"""
Command: db status.

Shows current migration status.
"""

from typer import Exit

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="status")
def status() -> None:
    """Show current migration status and pending changes."""
    print_section("Migration Status", "blue")
    rich_print("[bold blue]Checking migration status...[/bold blue]")

    try:
        rich_print("[cyan]Current revision:[/cyan]")
        run_command(["uv", "run", "alembic", "current"])

        rich_print("[cyan]Available heads:[/cyan]")
        run_command(["uv", "run", "alembic", "heads"])

        print_success("Status check complete")
    except Exception as e:
        print_error("Failed to get migration status")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
