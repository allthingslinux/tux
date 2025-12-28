"""
Command: tux start.

Starts the Tux Discord bot.
"""

import sys
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_info, print_section, print_success, rich_print
from tux.main import run

app = create_app()

# Constants
SUCCESS_EXIT_CODE: int = 0
USER_SHUTDOWN_EXIT_CODE: int = 130


@app.command(name="start")
def start(
    debug: Annotated[bool, Option("--debug", help="Enable debug mode")] = False,
) -> None:
    """Start the Tux Discord bot."""
    # Configure logging FIRST (before any other code runs)
    from tux.core.logging import configure_logging  # noqa: PLC0415
    from tux.shared.config import CONFIG  # noqa: PLC0415

    # Use --debug flag to override log level if provided
    log_level = "DEBUG" if debug else None
    configure_logging(level=log_level, config=CONFIG)

    print_section("Starting Tux Bot", "blue")
    rich_print("[bold blue]Starting Tux Discord bot...[/bold blue]")

    if debug:
        print_info("Debug mode enabled")

    exit_code = run()

    if exit_code == SUCCESS_EXIT_CODE:
        print_success("Bot completed successfully")
    elif exit_code == USER_SHUTDOWN_EXIT_CODE:
        print_info("Bot shutdown requested by user (Ctrl+C)")
    # For other exit codes, run() already logged the error

    sys.exit(exit_code)


if __name__ == "__main__":
    app()
