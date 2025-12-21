"""
Command: db history.

Shows migration history.
"""

from subprocess import CalledProcessError

from typer import Exit

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
    except CalledProcessError as e:
        print_error(f"Failed to get migration history: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
