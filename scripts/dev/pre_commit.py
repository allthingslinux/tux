"""
Command: dev pre-commit.

Runs pre-commit hooks.
"""

import sys

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="pre-commit")
def pre_commit() -> None:
    """Run pre-commit hooks to ensure code quality before commits."""
    print_section("Running Pre-commit Checks", "blue")

    try:
        run_command(["uv", "run", "pre-commit", "run", "--all-files"])
        print_success("Pre-commit checks completed successfully")
    except Exception:
        print_error("Pre-commit checks did not pass - see issues above")
        sys.exit(1)


if __name__ == "__main__":
    app()
