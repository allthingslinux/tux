"""
Command: docs serve.

Serves documentation locally with live reload.
"""

import os
import subprocess
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.docs.utils import has_zensical_config
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="serve")
def serve(
    dev_addr: Annotated[
        str,
        Option(
            "--dev-addr",
            "-a",
            help="IP address and port (default: localhost:8000)",
        ),
    ] = "localhost:8000",
    open_browser: Annotated[
        bool,
        Option("--open", "-o", help="Open preview in default browser"),
    ] = False,
    strict: Annotated[
        bool,
        Option("--strict", "-s", help="Strict mode"),
    ] = False,
) -> None:
    """Serve documentation locally with live reload."""
    print_section("Serving Documentation", "blue")

    if not has_zensical_config():
        return

    cmd = ["uv", "run", "zensical", "serve", "--dev-addr", dev_addr]
    if open_browser:
        cmd.append("--open")
    if strict:
        print_info("Warning: --strict mode is currently unsupported by zensical")
        cmd.append("--strict")

    try:
        print_info(f"Starting documentation server at {dev_addr}")
        subprocess.run(cmd, check=True, env=os.environ.copy())
    except subprocess.CalledProcessError:
        print_error("Failed to start documentation server")
    except KeyboardInterrupt:
        print_info("\nDocumentation server stopped")


if __name__ == "__main__":
    app()
