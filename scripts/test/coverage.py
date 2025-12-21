"""
Command: test coverage.

Generates coverage reports.
"""

import shlex
import sys
import webbrowser
from pathlib import Path
from subprocess import CalledProcessError
from typing import Annotated, Literal

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section

app = create_app()


def _build_coverage_cmd(
    specific: str | None,
    format_type: str | None,
    quick: bool,
    fail_under: int | None,
) -> list[str]:
    """Build the pytest coverage command."""
    cmd = ["uv", "run", "pytest", f"--cov={specific or 'src/tux'}"]

    if quick:
        cmd.append("--cov-report=")
    elif format_type:
        report_arg = "xml:coverage.xml" if format_type == "xml" else format_type
        cmd.append(f"--cov-report={report_arg}")

    if fail_under:
        cmd.extend(["--cov-fail-under", str(fail_under)])

    return cmd


def _handle_browser_opening(format_type: str | None) -> None:
    """Handle opening the coverage report in the browser."""
    if format_type == "html":
        html_report_path = Path("htmlcov/index.html")
        if html_report_path.exists():
            print_info("Opening HTML coverage report in browser...")
            try:
                webbrowser.open(f"file://{html_report_path.resolve()}")
            except Exception as e:
                print_error(f"Failed to open browser: {e}")
        else:
            print_error("HTML coverage report not found at htmlcov/index.html")
    elif format_type:
        print_info(
            f"Browser opening only supported for HTML format (current: {format_type})",
        )
    else:
        print_info(
            "Browser opening only supported for HTML format. Use --format html.",
        )


@app.command(name="coverage")
def coverage_report(
    specific: Annotated[
        str | None,
        Option("--specific", help="Path to include in coverage"),
    ] = None,
    format_type: Annotated[
        Literal["html", "xml", "json"] | None,
        Option("--format", help="Report format: html, xml, or json"),
    ] = None,
    quick: Annotated[
        bool,
        Option("--quick", help="Skip coverage report generation"),
    ] = False,
    fail_under: Annotated[
        int | None,
        Option("--fail-under", help="Minimum coverage percentage required"),
    ] = None,
    open_browser: Annotated[
        bool,
        Option(
            "--open",
            help="Automatically open browser for HTML coverage reports",
        ),
    ] = False,
) -> None:
    """Generate coverage reports."""
    print_section("Coverage Report", "blue")

    cmd = _build_coverage_cmd(specific, format_type, quick, fail_under)

    if quick and format_type:
        print_info("Note: --quick takes precedence; --format will be ignored")

    print_info(f"Running: {shlex.join(cmd)}")

    try:
        run_command(cmd, capture_output=False)

        if open_browser:
            _handle_browser_opening(format_type)

    except KeyboardInterrupt:
        print_info("\nCoverage generation interrupted by user")
        sys.exit(130)
    except CalledProcessError as e:
        print_error(f"Coverage report generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred during coverage generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
