"""
Command: docs wrangler-deployments.

Lists deployment history.
"""

from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="wrangler-deployments")
def wrangler_deployments(
    limit: Annotated[
        int,
        Option("--limit", "-l", help="Maximum number of deployments to show"),
    ] = 10,
) -> None:
    """List deployment history for the documentation site."""
    print_section("Deployment History", "blue")

    if not Path("wrangler.toml").exists():
        print_error("wrangler.toml not found. Please run from the project root.")
        return

    cmd = ["wrangler", "deployments", "list"]
    if limit:
        cmd.extend(["--limit", str(limit)])

    try:
        run_command(cmd, capture_output=False)
        print_success("Deployment history retrieved")
    except Exception as e:
        print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
