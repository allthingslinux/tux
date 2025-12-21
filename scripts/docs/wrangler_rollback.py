"""
Command: docs wrangler-rollback.

Rolls back to a previous deployment.
"""

from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, print_warning

app = create_app()


@app.command(name="wrangler-rollback")
def wrangler_rollback(
    version_id: Annotated[
        str,
        Option("--version-id", help="Version ID to rollback to"),
    ] = "",
    message: Annotated[
        str,
        Option("--message", "-m", help="Rollback message"),
    ] = "",
) -> None:
    """Rollback to a previous deployment."""
    print_section("Rolling Back Deployment", "blue")

    if not Path("wrangler.toml").exists():
        print_error("wrangler.toml not found. Please run from the project root.")
        return

    if not version_id:
        print_error(
            "Version ID is required. Use wrangler-deployments to find version IDs.",
        )
        return

    cmd = ["wrangler", "rollback", version_id]
    if message:
        cmd.extend(["--message", message])

    print_warning(f"Rolling back to version: {version_id}")

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Successfully rolled back to version {version_id}")
    except Exception as e:
        print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
