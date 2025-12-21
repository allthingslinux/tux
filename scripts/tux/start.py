"""
Command: tux start.

Starts the Tux Discord bot.
"""

import sys
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section, print_success, rich_print
from tux.main import run

app = create_app()


@app.command(name="start")
def start(
    debug: Annotated[bool, Option("--debug", help="Enable debug mode")] = False,
) -> None:
    """Start the Tux Discord bot."""
    print_section("Starting Tux Bot", "blue")
    rich_print("[bold blue]Starting Tux Discord bot...[/bold blue]")

    try:
        if debug:
            print_info("Debug mode enabled")

        exit_code = run()
        if exit_code == 0:
            print_success("Bot started successfully")
        elif exit_code == 130:
            print_info("Bot shutdown requested by user (Ctrl+C)")
        else:
            print_error(f"Bot exited with code {exit_code}")
            sys.exit(exit_code)

    except RuntimeError as e:
        if "setup failed" in str(e).lower():
            print_error("Bot setup failed")
            sys.exit(1)
        elif "Event loop stopped before Future completed" in str(e):
            print_info("Bot shutdown completed")
            sys.exit(0)
        else:
            print_error(f"Runtime error: {e}")
            sys.exit(1)
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        print_info("Bot shutdown requested by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print_error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
