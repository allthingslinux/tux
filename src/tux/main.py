"""
Tux Discord Bot Main Entry Point.

This module serves as the main entry point for the Tux Discord bot application.
It handles application initialization, error handling, and provides the run()
function that starts the bot with proper lifecycle management.
"""

import sys

from loguru import logger

from tux.core.app import TuxApp
from tux.shared.exceptions import TuxDatabaseError, TuxError


def run() -> int:
    """
    Instantiate and run the Tux application.

    This function is the entry point for the Tux application.
    It creates an instance of the TuxApp class.

    Returns
    -------
    int
        Exit code: 0 for success, non-zero for failure

    Notes
    -----
    Logging is configured by the CLI script (scripts/base.py) before this is called.
    """
    try:
        logger.info("🚀 Starting Tux...")
        app = TuxApp()
        return app.run()

    except (TuxDatabaseError, TuxError, SystemExit, KeyboardInterrupt, Exception) as e:
        # Handle all errors in one place
        if isinstance(e, TuxDatabaseError):
            logger.error("❌ Database connection failed")
            logger.info("💡 To start the database, run: make docker-up")
        elif isinstance(e, TuxError):
            logger.error(f"❌ Bot startup failed: {e}")
        elif isinstance(e, RuntimeError):
            logger.critical(f"❌ Application failed to start: {e}")
        elif isinstance(e, SystemExit):
            return int(e.code) if e.code is not None else 1
        elif isinstance(e, KeyboardInterrupt):
            logger.info("Shutdown requested by user")
            return 0
        else:
            logger.opt(exception=True).critical(f"Application failed to start: {e}")

        return 1

    else:
        return 0


if __name__ == "__main__":
    exit_code = run()
    sys.exit(exit_code)
