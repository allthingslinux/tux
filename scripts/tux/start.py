"""
Command: tux start.

Starts the Tux Discord bot.
"""

import sys
from enum import Enum, auto
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_info, print_section, print_success, rich_print
from tux.main import run

app = create_app()


class PostRunBehavior(Enum):
    """Behavior after the bot runs."""

    NORMAL = auto()  # Run generic status messages
    SKIP = auto()  # Messages already handled


def _run_bot(debug: bool) -> tuple[int, PostRunBehavior]:
    """Run the bot and return the exit code and post-run behavior."""
    if debug:
        print_info("Debug mode enabled")

    # The run() function in main.py already catches and logs exceptions
    # and returns a proper exit code.
    exit_code = run(debug=debug)

    # We assume run() has already handled the logging for errors and shutdowns
    return exit_code, PostRunBehavior.NORMAL


@app.command(name="start")
def start(
    debug: Annotated[bool, Option("--debug", help="Enable debug mode")] = False,
) -> None:
    """Start the Tux Discord bot."""
    print_section("Starting Tux Bot", "blue")
    rich_print("[bold blue]Starting Tux Discord bot...[/bold blue]")

    exit_code, behavior = _run_bot(debug)

    if behavior is PostRunBehavior.NORMAL:
        if exit_code == 0:
            print_success("Bot completed successfully")
        elif exit_code == 130:
            print_info("Bot shutdown requested by user (Ctrl+C)")
        else:
            # We don't print a generic error here because run() already logged it
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    app()
