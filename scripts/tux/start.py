"""
Command: tux start.

Starts the Tux Discord bot.
"""

import sys
from enum import Enum, auto
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section, print_success, rich_print
from tux.main import run

app = create_app()


class PostRunBehavior(Enum):
    """Behavior after the bot runs."""

    NORMAL = auto()  # Run generic status messages
    SKIP = auto()  # Messages already handled


def _run_bot(debug: bool) -> tuple[int, PostRunBehavior]:
    """Run the bot and handle exceptions."""
    exit_code = 1
    behavior = PostRunBehavior.SKIP

    try:
        if debug:
            print_info("Debug mode enabled")

        exit_code = run(debug=debug)
        behavior = PostRunBehavior.NORMAL
    except RuntimeError as e:
        msg = str(e)
        if "setup failed" in msg.lower():
            print_error("Bot setup failed")
        elif "Event loop stopped before Future completed" in msg:
            print_info("Bot shutdown completed")
            exit_code = 0
        else:
            print_error(f"Runtime error: {e}")
    except KeyboardInterrupt:
        print_info("Bot shutdown requested by user (Ctrl+C)")
        exit_code = 130
    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 1
    except Exception as e:
        print_error(f"Failed to start bot: {e}")

    return exit_code, behavior


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
            print_success("Bot started successfully")
        elif exit_code == 130:
            print_info("Bot shutdown requested by user (Ctrl+C)")
        else:
            print_error(f"Bot exited with code {exit_code}")

    sys.exit(exit_code)


if __name__ == "__main__":
    app()
