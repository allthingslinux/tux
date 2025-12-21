"""
Command: docs serve.

Serves documentation locally with live reload.
"""

from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.utils import has_zensical_config
from scripts.proc import run_command
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
        raise Exit(1)

    cmd = ["uv", "run", "zensical", "serve", "--dev-addr", dev_addr]
    if open_browser:
        cmd.append("--open")
    if strict:
        print_error("--strict mode is not yet supported by zensical")
        raise Exit(1)

    try:
        print_info(f"Starting documentation server at {dev_addr}")
        # Using run_command for consistency and logging
        run_command(cmd, capture_output=False)
    except KeyboardInterrupt:
        print_info("\nDocumentation server stopped")
    except Exception as e:
        print_error(f"Failed to start documentation server: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
