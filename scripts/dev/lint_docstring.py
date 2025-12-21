"""
Command: dev lint-docstring.

Lints docstrings for proper formatting.
"""

import sys

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="lint-docstring")
def lint_docstring() -> None:
    """Lint docstrings for proper formatting and completeness."""
    print_section("Linting Docstrings", "blue")

    try:
        run_command(["uv", "run", "pydoclint", "--config=pyproject.toml", "."])
        print_success("Docstring linting completed successfully")
    except Exception:
        print_error("Docstring linting did not pass - see issues above")
        sys.exit(1)


if __name__ == "__main__":
    app()
