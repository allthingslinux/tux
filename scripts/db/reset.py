"""
Command: db reset.

Resets the database to a clean state via migrations.
"""

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="reset")
def reset() -> None:
    """Reset database to clean state via migrations."""
    print_section("Reset Database", "yellow")
    rich_print("[bold yellow]This will reset your database![/bold yellow]")
    rich_print("[yellow]Downgrading to base and reapplying all migrations...[/yellow]")

    try:
        run_command(["uv", "run", "alembic", "downgrade", "base"])
        run_command(["uv", "run", "alembic", "upgrade", "head"])
        print_success("Database reset and migrations reapplied!")
    except Exception:
        print_error("Failed to reset database")


if __name__ == "__main__":
    app()
