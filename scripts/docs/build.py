"""
Command: docs build.

Builds documentation site for production.
"""

from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.utils import has_zensical_config
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section, print_success

app = create_app()


@app.command(name="build")
def build(
    clean: Annotated[
        bool,
        Option("--clean", "-c", help="Clean cache"),
    ] = False,
    strict: Annotated[
        bool,
        Option("--strict", "-s", help="Strict mode"),
    ] = False,
) -> None:
    """Build documentation site for production."""
    print_section("Building Documentation", "blue")

    if not has_zensical_config():
        raise Exit(1)

    cmd = ["uv", "run", "zensical", "build"]
    if clean:
        cmd.append("--clean")
    if strict:
        cmd.append("--strict")

    try:
        print_info("Building documentation...")
        run_command(cmd, capture_output=False)
        print_success("Documentation built successfully")
    except Exception as e:
        print_error(f"Failed to build documentation: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
