"""
Command: test benchmark.

Runs benchmark tests.
"""

import os

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="benchmark")
def benchmark_tests() -> None:
    """Run benchmark tests."""
    print_section("Benchmark Tests", "blue")
    cmd = ["uv", "run", "pytest", "--benchmark-only", "--benchmark-sort=mean"]
    print_info(f"Running: {' '.join(cmd)}")
    try:
        os.execvp(cmd[0], cmd)
    except OSError as e:
        print_error(f"Failed to execute command: {e}")
        raise


if __name__ == "__main__":
    app()
