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
            help="Load balancing scope: module, class, or function (default: module)",
        ),
    ] = None,
) -> None:
    """Run tests in parallel using pytest-xdist."""
    print_section("Parallel Tests (pytest-xdist)", "blue")
    cmd = ["uv", "run", "pytest"]

    if workers is None:
        cmd.extend(["-n", "auto"])
    else:
        cmd.extend(["-n", str(workers)])

    if load_scope:
        cmd.extend(["--dist", load_scope])

    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvp(cmd[0], cmd)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
