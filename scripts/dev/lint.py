"""
Command: dev lint.

Runs linting checks with Ruff.
"""

import sys
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section, print_success

app = create_app()


@app.command(name="lint")
def lint(
    fix: Annotated[bool, Option("--fix", help="Automatically apply fixes")] = False,
) -> None:
    """Run linting checks with Ruff to ensure code quality."""
    print_section("Running Linting", "blue")
    print_info("Checking code quality with Ruff...")

    cmd = ["uv", "run", "ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.append(".")

    try:
        run_command(cmd)
        print_success("Linting completed successfully")
    except Exception:
        print_error("Linting did not pass - see issues above")
        sys.exit(1)


if __name__ == "__main__":
    app()
