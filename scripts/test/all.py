"""
Command: test all.

Runs all tests with coverage.
"""

import os

from scripts.core import create_app
from scripts.ui import print_info, print_section

app = create_app()


@app.command(name="all")
def all_tests() -> None:
    """Run all tests with coverage."""
    print_section("Running Tests", "blue")
    # Set PYTHONDONTWRITEBYTECODE for faster test execution
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = ["uv", "run", "pytest"]
    print_info(f"Running: {' '.join(cmd)}")
    os.execvpe(cmd[0], cmd, env)


if __name__ == "__main__":
    app()
