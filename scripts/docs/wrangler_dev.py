"""
Command: docs wrangler-dev.

Starts local Wrangler development server.
"""

from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.docs.build import build
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section, print_success

app = create_app()


@app.command(name="wrangler-dev")
def wrangler_dev(
    port: Annotated[int, Option("--port", "-p", help="Port to serve on")] = 8787,
    remote: Annotated[
        bool,
        Option("--remote", help="Run on remote Cloudflare infrastructure"),
    ] = False,
) -> None:
    """Start local Wrangler development server."""
    print_section("Starting Wrangler Dev Server", "blue")

    if not Path("wrangler.toml").exists():
        print_error("wrangler.toml not found. Please run from the project root.")
        return

    print_info("Building documentation...")

    build(strict=True)

    cmd = ["wrangler", "dev", f"--port={port}"]
    if remote:
        cmd.append("--remote")

    print_info(f"Starting Wrangler dev server on port {port}...")

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Wrangler dev server started at http://localhost:{port}")
    except Exception as e:
        print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
