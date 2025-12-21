"""
Command: dev type-check.

Performs static type checking using basedpyright.
"""

import sys
from subprocess import CalledProcessError

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()


@app.command(name="type-check")
def type_check() -> None:
    """Perform static type checking using basedpyright."""
    print_section("Type Checking", "blue")

    try:
        run_command(["uv", "run", "basedpyright"])
        print_success("Type checking completed successfully")
    except CalledProcessError as e:
        print_error(f"Type checking failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
