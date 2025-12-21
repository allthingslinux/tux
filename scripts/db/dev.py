"""
Command: db dev.

Development workflow: create and optionally apply a new migration.
"""

from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="dev")
def dev(
    create_only: Annotated[
        bool,
        Option("--create-only", help="Create migration but don't apply it"),
    ] = False,
    name: Annotated[
        str | None,
        Option("--name", "-n", help="Name for the migration"),
    ] = None,
) -> None:
    """Development workflow: create migration and apply it."""
    print_section("Development Workflow", "blue")

    migration_name = name or "dev migration"

    try:
        if create_only:
            rich_print("[bold blue]Creating migration only...[/bold blue]")
            run_command(
                [
                    "uv",
                    "run",
                    "alembic",
                    "revision",
                    "--autogenerate",
                    "-m",
                    migration_name,
                ],
            )
            print_success("Migration created - review and apply with 'db push'")
        else:
            rich_print("[bold blue]Creating and applying migration...[/bold blue]")
            run_command(
                [
                    "uv",
                    "run",
                    "alembic",
                    "revision",
                    "--autogenerate",
                    "-m",
                    migration_name,
                ],
            )
            run_command(["uv", "run", "alembic", "upgrade", "head"])
            print_success("Migration created and applied!")
    except Exception:
        print_error("Failed to create migration")
        raise Exit(1) from None


if __name__ == "__main__":
    app()
