"""
Command: db current.

Shows the current revision and optionally checks if all head revisions are applied.
"""

from subprocess import CalledProcessError

from typer import Exit, Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


@app.command(name="current")
def current(
    check_heads: bool = Option(
        False,
        "--check-heads",
        help="Check if all head revisions are applied",
    ),
) -> None:
    """Show current database revision and optionally check heads."""
    print_section("Current Revision", "blue")

    try:
        cmd = ["uv", "run", "alembic", "current"]
        if check_heads:
            cmd.append("--check-heads")
            rich_print(
                "[bold blue]Checking if all head revisions are applied...[/bold blue]",
            )
        else:
            rich_print("[bold blue]Showing current revision...[/bold blue]")

        run_command(cmd)

        if check_heads:
            print_success("All head revisions are applied!")
        else:
            print_success("Current revision displayed!")

    except CalledProcessError as e:
        if check_heads:
            print_error(f"Head revision check failed: {e}")
        else:
            print_error(f"Failed to show current revision: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
