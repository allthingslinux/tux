"""
Command: test quick.

Runs tests without coverage (faster).
"""

import os

from scripts.core import create_app
from scripts.ui import print_info, print_section

app = create_app()


@app.command(name="quick")
def quick_tests() -> None:
    """Run tests without coverage (faster)."""
    print_section("Quick Tests", "blue")
    cmd = ["uv", "run", "pytest", "--no-cov"]
    print_info(f"Running: {' '.join(cmd)}")
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    app()
