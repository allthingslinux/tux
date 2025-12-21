"""
Command: docs wrangler-dev.

Starts local Wrangler development server.
"""

from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.build import build
from scripts.docs.utils import has_wrangler_config
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section

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

    if not has_wrangler_config():
        raise Exit(1)

    print_info("Building documentation...")
    # build(strict=True) already handles errors and raises Exit(1)
    build(strict=True)

    cmd = ["wrangler", "dev", f"--port={port}"]
    if remote:
        cmd.append("--remote")

    print_info(f"Starting Wrangler dev server on port {port}...")
    print_info("Press Ctrl+C to stop the server")

    try:
        run_command(cmd, capture_output=False)
    except KeyboardInterrupt:
        print_info("\nWrangler dev server stopped")
        raise Exit(0) from None
    except Exception as e:
        print_error(f"Wrangler dev server failed: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
