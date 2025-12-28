"""
Command: dev lint-fix.

Runs linting checks with Ruff and automatically applies fixes.
"""

import subprocess
import sys

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="lint-fix")
def lint_fix() -> None:
    """Run linting checks with Ruff and automatically apply fixes."""
    print_section("Running Linting with Fixes", "blue")

    try:
        run_command(["uv", "run", "ruff", "check", "--fix", "."])
        print_success("Linting with fixes completed successfully")
    except subprocess.CalledProcessError:
        print_error("Linting with fixes did not complete - see issues above")
        sys.exit(1)
    except (FileNotFoundError, PermissionError, OSError) as e:
        print_error(f"Failed to run linting tool: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
