"""
Command: test html.

Runs tests and generates an HTML report.
"""

import shlex
import sys
import webbrowser
from pathlib import Path
from subprocess import CalledProcessError
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section, print_warning

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
    report_path = "reports/test_report.html"
    cmd = [
        "uv",
        "run",
        "pytest",
        "--cov-report=html",
        f"--html={report_path}",
        "--self-contained-html",
    ]

    print_info(f"Running: {shlex.join(cmd)}")

    try:
        run_command(cmd, capture_output=False)

        if open_browser:
            html_report_path = Path(report_path)
            if html_report_path.exists():
                print_info(f"Opening HTML report in browser: {report_path}")
                try:
                    webbrowser.open(f"file://{html_report_path.resolve()}")
                except Exception as e:
                    print_warning(f"Failed to open browser: {e}")
            else:
                print_warning(f"HTML report not found at {report_path}")

    except KeyboardInterrupt:
        print_info("\nTests interrupted by user")
        sys.exit(130)
    except CalledProcessError as e:
        print_error(f"Tests failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred during HTML report generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
