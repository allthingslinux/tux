"""
Command: db new.

Generates a new migration from model changes.
"""

from subprocess import CalledProcessError
from typing import Annotated

from typer import Argument, Exit, Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="new")
def new(
    message: Annotated[
        str,
        Argument(help="Descriptive message for the migration", metavar="MESSAGE"),
    ],
    auto_generate: Annotated[
        bool,
        Option("--auto/--no-auto", help="Auto-generate migration from model changes"),
    ] = True,
) -> None:
    """Generate new migration from model changes."""
    print_section("New Migration", "blue")
    rich_print(f"[bold blue]Generating migration: {message}[/bold blue]")

    cmd = ["uv", "run", "alembic", "revision"]
    if auto_generate:
        cmd.append("--autogenerate")
    cmd.extend(["-m", message])

    try:
        run_command(cmd)
        print_success(f"Migration generated: {message}")
        rich_print("[yellow]Review the migration file before applying[/yellow]")
    except CalledProcessError as e:
        print_error(f"Failed to generate migration: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
