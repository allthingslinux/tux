"""
Command: docs wrangler-tail.

Views real-time logs from deployed docs.
"""

import os
import subprocess
from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section

app = create_app()


@app.command(name="wrangler-tail")
def wrangler_tail(
    format_output: Annotated[
        str,
        Option("--format", help="Output format: json or pretty"),
    ] = "pretty",
    status: Annotated[
        str,
        Option("--status", help="Filter by status: ok, error, or canceled"),
    ] = "",
) -> None:
    """View real-time logs from deployed documentation."""
    print_section("Tailing Logs", "blue")

    if not Path("wrangler.toml").exists():
        print_error("wrangler.toml not found. Please run from the project root.")
        return

    cmd = ["wrangler", "tail"]
    if format_output:
        cmd.extend(["--format", format_output])
    if status:
        cmd.extend(["--status", status])

    print_info("Starting log tail... (Ctrl+C to stop)")

    try:
        subprocess.run(cmd, check=True, env=os.environ.copy())
    except subprocess.CalledProcessError:
        print_error("Failed to tail logs")
    except KeyboardInterrupt:
        print_info("\nLog tail stopped")
    except Exception as e:
        print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
