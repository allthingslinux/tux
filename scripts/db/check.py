"""
Command: db check.

Validates migration files.
"""

from subprocess import CalledProcessError

from typer import Exit

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="check")
def check() -> None:
    """Validate migration files for correctness."""
    print_section("Validate Migrations", "blue")
    rich_print("[bold blue]Checking migration files for issues...[/bold blue]")

    try:
        run_command(["uv", "run", "alembic", "check"])
        print_success("All migrations validated successfully!")
    except CalledProcessError as e:
        print_error(f"Migration validation failed: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
