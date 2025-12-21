"""
Command: docs wrangler-versions.

Lists and manages versions.
"""

from subprocess import CalledProcessError
from typing import Annotated, Literal

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.utils import has_wrangler_config
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="wrangler-versions")
def wrangler_versions(
    action: Annotated[
        Literal["list", "view", "upload"],
        Option("--action", "-a", help="Action to perform"),
    ] = "list",
    version_id: Annotated[
        str,
        Option("--version-id", help="Version ID to view (required for 'view')"),
    ] = "",
    alias: Annotated[
        str,
        Option("--alias", help="Preview alias name (required for 'upload')"),
    ] = "",
) -> None:
    """List and manage versions of the documentation."""
    print_section("Managing Versions", "blue")

    if not has_wrangler_config():
        raise Exit(1)

    if action == "view" and not version_id:
        print_error("The --version-id option is required when --action view is used.")
        raise Exit(1)

    if action == "upload" and not alias:
        print_error("The --alias option is required when --action upload is used.")
        raise Exit(1)

    cmd = ["wrangler", "versions", action]

    if action == "view":
        cmd.append(version_id)
    elif action == "upload":
        cmd.extend(["--preview-alias", alias])

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Version {action} completed")
    except CalledProcessError as e:
        print_error(f"Version {action} failed: {e}")
        raise Exit(1) from e
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
