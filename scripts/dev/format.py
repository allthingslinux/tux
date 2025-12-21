"""
Command: dev format.

Formats code using Ruff's formatter.
"""

import sys

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="format")
def format_code() -> None:
    """Format code using Ruff's formatter for consistent styling."""
    print_section("Formatting Code", "blue")

    try:
        run_command(["uv", "run", "ruff", "format", "."])
        print_success("Code formatting completed successfully")
    except Exception:
        print_error("Code formatting did not pass - see issues above")
        sys.exit(1)


if __name__ == "__main__":
    app()
