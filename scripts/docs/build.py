"""
Command: docs build.

Builds documentation site for production.
"""

import os
import subprocess
from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section, print_success

app = create_app()


def _find_zensical_config() -> str | None:
    current_dir = Path.cwd()
    if (current_dir / "zensical.toml").exists():
        return "zensical.toml"
    print_error("Can't find zensical.toml file. Please run from the project root.")
    return None


@app.command(name="build")
def build(
    clean: Annotated[
        bool,
        Option("--clean", "-c", help="Clean cache"),
    ] = False,
    strict: Annotated[
        bool,
        Option("--strict", "-s", help="Strict mode (currently unsupported)"),
    ] = False,
) -> None:
    """Build documentation site for production."""
    print_section("Building Documentation", "blue")

    if not _find_zensical_config():
        return

    cmd = ["uv", "run", "zensical", "build"]
    if clean:
        cmd.append("--clean")
    if strict:
        cmd.append("--strict")

    try:
        print_info("Building documentation...")
        subprocess.run(cmd, check=True, env=os.environ.copy())
        print_success("Documentation built successfully")
    except subprocess.CalledProcessError:
        print_error("Failed to build documentation")
    except KeyboardInterrupt:
        print_info("\nBuild interrupted")


if __name__ == "__main__":
    app()
