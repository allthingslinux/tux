"""
Command: dev docstring-coverage.

Checks docstring coverage across the codebase.
"""

from subprocess import CalledProcessError

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success

app = create_app()

# Constants
ERROR_EXIT_CODE_THRESHOLD = 100


@app.command(name="docstring-coverage")
def docstring_coverage() -> None:
    """Check docstring coverage across the codebase."""
    print_section("Docstring Coverage", "blue")

    try:
        run_command(["uv", "run", "docstr-coverage", "--verbose", "2", "."])
        print_success("Docstring coverage report generated")
    except CalledProcessError as e:
        # docstr-coverage returns non-zero if coverage is below threshold
        # Exit codes 1-99 typically indicate coverage issues (show report)
        # Exit codes 100+ indicate actual errors
        if e.returncode < ERROR_EXIT_CODE_THRESHOLD:
            print_success(
                "Docstring coverage report generated (coverage below threshold)",
            )
        else:
            print_error(f"Error running docstring coverage: {e}")
            raise


if __name__ == "__main__":
    app()
