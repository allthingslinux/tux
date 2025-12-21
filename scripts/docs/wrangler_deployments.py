"""
Command: docs wrangler-deployments.

Lists deployment history.
"""

from subprocess import CalledProcessError
from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.utils import has_wrangler_config
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

    if not has_wrangler_config():
        raise Exit(1)

    cmd = ["wrangler", "deployments", "list"]
    if limit:
        cmd.extend(["--limit", str(limit)])

    try:
        run_command(cmd, capture_output=False)
        print_success("Deployment history retrieved")
    except CalledProcessError as e:
        print_error(f"Failed to retrieve deployment history: {e}")
        raise Exit(1) from e
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
