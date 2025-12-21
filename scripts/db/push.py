"""
Command: db push.

Applies pending migrations to the database.
"""

from subprocess import CalledProcessError

from typer import Exit

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="push")
def push() -> None:
    """Apply pending migrations to database."""
    print_section("Apply Migrations", "blue")
    rich_print("[bold blue]Applying pending migrations...[/bold blue]")

    try:
        run_command(["uv", "run", "alembic", "upgrade", "head"])
        print_success("All migrations applied!")
    except CalledProcessError as e:
        print_error(f"Failed to apply migrations: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
