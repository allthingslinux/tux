"""
Command: test html.

Runs tests and generates an HTML report.
"""

import webbrowser
from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_info, print_section

app = create_app()


@app.command(name="html")
def html_report(
    open_browser: Annotated[
        bool,
        Option("--open", help="Automatically open browser with HTML report"),
    ] = False,
) -> None:
    """Run tests and generate HTML report."""
    print_section("HTML Report", "blue")
    cmd = [
        "uv",
        "run",
        "pytest",
        "--cov-report=html",
        "--html=reports/test_report.html",
        "--self-contained-html",
    ]

    print_info(f"Running: {' '.join(cmd)}")

    try:
        run_command(cmd, capture_output=False)
        if open_browser:
            html_report_path = Path("htmlcov/index.html")
            if html_report_path.exists():
                print_info("Opening HTML coverage report in browser...")
                webbrowser.open(f"file://{html_report_path.resolve()}")
    except Exception:
        pass


if __name__ == "__main__":
    app()
