"""
Command: dev pre-commit.

Runs pre-commit hooks.
"""

import sys
from subprocess import CalledProcessError

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
    except CalledProcessError as e:
        print_error(f"Pre-commit checks did not pass: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred during pre-commit checks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
