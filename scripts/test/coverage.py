"""
Command: test coverage.

Generates coverage reports.
"""

import webbrowser
from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_info, print_section

app = create_app()


@app.command(name="coverage")
def coverage_report(
    specific: Annotated[
        str | None,
        Option("--specific", help="Path to include in coverage"),
    ] = None,
    format_type: Annotated[
        str | None,
        Option("--format", help="Report format: html, xml, or json"),
    ] = None,
    quick: Annotated[
        bool,
        Option("--quick", help="Skip coverage report generation"),
    ] = False,
    fail_under: Annotated[
        str | None,
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

    cmd = ["uv", "run", "pytest"]

    if specific:
        cmd.append(f"--cov={specific}")

    if quick:
        cmd.append("--cov-report=")
    elif format_type:
        match format_type:
            case "html":
                cmd.append("--cov-report=html")
            case "xml":
                cmd.append("--cov-report=xml:coverage.xml")
            case "json":
                cmd.append("--cov-report=json")
            case _:
                pass

    if fail_under:
        cmd.extend(["--cov-fail-under", fail_under])

    print_info(f"Running: {' '.join(cmd)}")

    try:
        run_command(cmd, capture_output=False)

        if open_browser and format_type == "html":
            html_report_path = Path("htmlcov/index.html")
            if html_report_path.exists():
                print_info("Opening HTML coverage report in browser...")
                webbrowser.open(f"file://{html_report_path.resolve()}")
    except Exception:
        pass


if __name__ == "__main__":
    app()
