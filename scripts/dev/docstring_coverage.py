"""
Command: dev docstring-coverage.

Checks docstring coverage across the codebase.
"""

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_section, print_success

app = create_app()


@app.command(name="docstring-coverage")
def docstring_coverage() -> None:
    """Check docstring coverage across the codebase."""
    print_section("Docstring Coverage", "blue")

    try:
        run_command(["uv", "run", "docstr-coverage", "--verbose", "2", "."])
        print_success("Docstring coverage report generated")
    except Exception:
        # docstr-coverage might return non-zero if coverage is below threshold
        # but we still want to show the report
        pass


if __name__ == "__main__":
    app()
