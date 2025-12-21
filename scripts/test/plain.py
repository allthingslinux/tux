"""
Command: test plain.

Runs tests with plain output.
"""

import os

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="plain")
def plain_tests() -> None:
    """Run tests with plain output."""
    print_section("Plain Tests", "blue")
    cmd = ["uv", "run", "pytest", "-p", "no:sugar"]
    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvp(cmd[0], cmd)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        raise


if __name__ == "__main__":
    app()
