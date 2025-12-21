"""
Command: docs wrangler-tail.

Views real-time logs from deployed docs.
"""

from enum import Enum
from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.utils import has_wrangler_config
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section

app = create_app()


class OutputFormat(str, Enum):
    """Output formats for wrangler tail."""

    JSON = "json"
    PRETTY = "pretty"


class LogStatus(str, Enum):
    """Log status filters for wrangler tail."""

    OK = "ok"
    ERROR = "error"
    CANCELED = "canceled"


@app.command(name="wrangler-tail")
def wrangler_tail(
    format_output: Annotated[
        OutputFormat | None,
        Option("--format", help="Output format: json or pretty"),
    ] = None,
    status: Annotated[
        LogStatus | None,
        Option("--status", help="Filter by status: ok, error, or canceled"),
    ] = None,
) -> None:
    """View real-time logs from deployed documentation."""
    print_section("Tailing Logs", "blue")

    if not has_wrangler_config():
        raise Exit(1)

    cmd = ["wrangler", "tail"]
    if format_output:
        cmd.extend(["--format", format_output.value])
    if status:
        cmd.extend(["--status", status.value])

    print_info("Starting log tail... (Ctrl+C to stop)")

    try:
        run_command(cmd, capture_output=False)
    except Exception as e:
        print_error(f"Failed to tail logs: {e}")
        raise Exit(1) from e
    except KeyboardInterrupt:
        print_info("\nLog tail stopped")
        raise Exit(0) from None


if __name__ == "__main__":
    app()
