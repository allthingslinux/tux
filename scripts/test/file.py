"""
Command: test file.

Runs specific test files or paths.
"""

import os
from typing import Annotated

from typer import Argument, Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="file")
def file_tests(
    test_paths: Annotated[
        list[str],
        Argument(help="Test file paths, directories, or pytest node IDs"),
    ],
    coverage: Annotated[
        bool,
        Option("--coverage", "-c", help="Enable coverage collection"),
    ] = False,
) -> None:
    """Run specific test files or paths."""
    print_section("Running Tests", "blue")
    cmd = ["uv", "run", "pytest"]
    if not coverage:
        cmd.append("--no-cov")
    cmd.extend(test_paths)

    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvp(cmd[0], cmd)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        raise


if __name__ == "__main__":
    app()
