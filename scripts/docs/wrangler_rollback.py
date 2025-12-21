"""
Command: docs wrangler-rollback.

Rolls back to a previous deployment.
"""

from typing import Annotated

from typer import Argument, Exit, Option

from scripts.core import create_app
from scripts.docs.utils import has_wrangler_config
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, print_warning

app = create_app()


@app.command(name="wrangler-rollback")
def wrangler_rollback(
    version_id: Annotated[
        str,
        Argument(help="Version ID to rollback to"),
    ],
    message: Annotated[
        str,
        Option("--message", "-m", help="Rollback message"),
    ] = "",
) -> None:
    """Rollback to a previous deployment."""
    print_section("Rolling Back Deployment", "blue")

    if not has_wrangler_config():
        raise Exit(1)

    cmd = ["wrangler", "rollback", version_id]
    if message:
        cmd.extend(["--message", message])

    print_warning(f"Rolling back to version: {version_id}")

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Successfully rolled back to version {version_id}")
    except Exception as e:
        print_error(f"Error: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
