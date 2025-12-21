"""
Command: test benchmark.

Runs benchmark tests.
"""

import os

from scripts.core import create_app
from scripts.ui import print_info, print_section

app = create_app()


@app.command(name="benchmark")
def benchmark_tests() -> None:
    """Run benchmark tests."""
    print_section("Benchmark Tests", "blue")
    cmd = ["uv", "run", "pytest", "--benchmark-only", "--benchmark-sort=mean"]
    print_info(f"Running: {' '.join(cmd)}")
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    app()
