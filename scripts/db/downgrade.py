"""
Command: db downgrade.

Rolls back to a previous migration revision.
"""

import sys
from subprocess import CalledProcessError
from typing import Annotated

from typer import Argument, Option, confirm

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import (
    print_error,
    print_info,
    print_section,
    print_success,
    rich_print,
)

app = create_app()


@app.command(name="downgrade")
def downgrade(
    revision: Annotated[
        str,
        Argument(
            help="Revision to downgrade to (e.g., '-1' for one step back, 'base' for initial state, or specific revision ID)",
        ),
    ],
    force: Annotated[
        bool,
        Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Rollback to a previous migration revision."""
    print_section("Downgrade Database", "yellow")
    rich_print(f"[bold yellow]Rolling back to revision: {revision}[/bold yellow]")
    rich_print(
        "[yellow]This may cause data loss. Backup your database first.[/yellow]\n",
    )

    if not force and not confirm(f"Downgrade to {revision}?", default=False):
        print_info("Downgrade cancelled")
        return

    try:
        run_command(["uv", "run", "alembic", "downgrade", revision])
        print_success(f"Successfully downgraded to revision: {revision}")
    except CalledProcessError as e:
        print_error(f"Failed to downgrade to revision {revision}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
