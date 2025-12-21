"""
Command: db history.

Shows migration history.
"""

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="history")
def history() -> None:
    """Show migration history with detailed tree view."""
    print_section("Migration History", "blue")
    rich_print("[bold blue]Showing migration history...[/bold blue]")

    try:
        run_command(["uv", "run", "alembic", "history", "--verbose"])
        print_success("History displayed")
    except Exception:
        print_error("Failed to get migration history")


if __name__ == "__main__":
    app()
