"""
Command: db version.

Shows version information for database components.
"""

import sys
from subprocess import CalledProcessError

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="version")
def version() -> None:
    """Show version information for database components."""
    print_section("Version Information", "blue")
    rich_print("[bold blue]Showing database version information...[/bold blue]")

    try:
        rich_print("[cyan]Current migration:[/cyan]")
        run_command(["uv", "run", "alembic", "current"])

        rich_print("[cyan]Database driver:[/cyan]")
        run_command(
            [
                "uv",
                "run",
                "python",
                "-c",
                "import psycopg; print(f'psycopg version: {psycopg.__version__}')",
            ],
        )

        print_success("Version information displayed")
    except CalledProcessError:
        print_error("Failed to get version information")
        sys.exit(1)
    except Exception:
        print_error("An unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    app()
