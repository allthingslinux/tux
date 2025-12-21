"""
Command: db check.

Validates migration files.
"""

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
    except Exception:
        print_error("Migration validation failed - check your migration files")


if __name__ == "__main__":
    app()
