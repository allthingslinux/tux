"""
Command: db show.

Shows details of a specific migration.
"""

from subprocess import CalledProcessError
from typing import Annotated

from typer import Argument, Exit

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="show")
def show(
    revision: Annotated[
        str,
        Argument(
            help="Migration revision ID to show (e.g., 'head', 'base', or specific ID)",
        ),
    ],
) -> None:
    """Show details of a specific migration."""
    print_section("Show Migration", "blue")
    rich_print(f"[bold blue]Showing migration: {revision}[/bold blue]")

    try:
        run_command(["uv", "run", "alembic", "show", revision])
        print_success(f"Migration details displayed for: {revision}")
    except CalledProcessError as e:
        print_error(f"Failed to show migration '{revision}': {e}")
        raise Exit(1) from e
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
