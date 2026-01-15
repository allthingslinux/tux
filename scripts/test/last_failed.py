"""
Command: test last-failed.

Runs only tests that failed in the last test run (faster iteration).
"""

import os

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="last-failed")
def last_failed_tests() -> None:
    """Run only tests that failed in the last test run (faster iteration)."""
    print_section("Last Failed Tests", "blue")
    # Set PYTHONDONTWRITEBYTECODE for faster test execution
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = ["uv", "run", "pytest", "--lf", "--no-cov"]
    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvpe(cmd[0], cmd, env)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        raise


if __name__ == "__main__":
    app()
