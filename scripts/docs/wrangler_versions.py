"""
Command: docs wrangler-versions.

Lists and manages versions.
"""

from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="wrangler-versions")
def wrangler_versions(
    action: Annotated[
        str,
        Option("--action", "-a", help="Action to perform: list, view, or upload"),
    ] = "list",
    version_id: Annotated[
        str,
        Option("--version-id", help="Version ID to view"),
    ] = "",
    alias: Annotated[
        str,
        Option("--alias", help="Preview alias name"),
    ] = "",
) -> None:
    """List and manage versions of the documentation."""
    print_section("Managing Versions", "blue")

    if not Path("wrangler.toml").exists():
        print_error("wrangler.toml not found. Please run from the project root.")
        return

    cmd = ["wrangler", "versions", action]

    if action == "view" and version_id:
        cmd.append(version_id)
    elif action == "upload" and alias:
        cmd.extend(["--preview-alias", alias])

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Version {action} completed")
    except Exception as e:
        print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
