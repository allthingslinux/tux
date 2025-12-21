"""
Command: test parallel.

Runs tests in parallel using pytest-xdist.
"""

import os
import sys
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="parallel")
def parallel_tests(
    workers: Annotated[
        int | None,
        Option(
            "--workers",
            "-n",
            help="Number of parallel workers (default: auto, uses CPU count)",
        ),
    ] = None,
    load_scope: Annotated[
        str | None,
        Option(
            "--load-scope",
            help="Distribution mode: load, loadscope, loadfile, loadgroup, worksteal, or no (default: loadscope)",
        ),
    ] = None,
) -> None:
    """Run tests in parallel using pytest-xdist."""
    # Validate workers
    if workers is not None and workers <= 0:
        print_error("Workers must be a positive integer")
        sys.exit(1)

    # Validate load_scope
    valid_scopes = {"load", "loadscope", "loadfile", "loadgroup", "worksteal", "no"}
    if load_scope is not None and load_scope not in valid_scopes:
        print_error(f"Invalid load scope. Must be one of: {', '.join(valid_scopes)}")
        sys.exit(1)

    print_section("Parallel Tests (pytest-xdist)", "blue")
    cmd = ["uv", "run", "pytest"]

    if workers is None:
        cmd.extend(["-n", "auto"])
    else:
        cmd.extend(["-n", str(workers)])

    if load_scope:
        cmd.extend(["--dist", load_scope])
    else:
        # Default to loadscope for better stability with our fixtures
        cmd.extend(["--dist", "loadscope"])

    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvp(cmd[0], cmd)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
