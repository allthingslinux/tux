"""
Command: test fast.

Runs tests excluding slow tests (faster local development).
"""

import os

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="fast")
def fast_tests() -> None:
    """Run tests excluding slow tests (faster local development)."""
    print_section("Fast Tests (excluding slow)", "blue")
    # Set PYTHONDONTWRITEBYTECODE for faster test execution
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = ["uv", "run", "pytest", "-m", "not slow", "--no-cov"]
    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvpe(cmd[0], cmd, env)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        raise


if __name__ == "__main__":
    app()
