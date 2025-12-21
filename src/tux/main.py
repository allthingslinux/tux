"""
Tux Discord Bot Main Entry Point.

This module serves as the main entry point for the Tux Discord bot application.
It handles application initialization, error handling, and provides the run()
function that starts the bot with proper lifecycle management.
"""

from loguru import logger

from tux.core.app import TuxApp
from tux.shared.exceptions import (
    TuxDatabaseError,
    TuxError,
    TuxGracefulShutdown,
    TuxSetupError,
)


def run(debug: bool = False) -> int:
    """
    Instantiate and run the Tux application.

    This function is the entry point for the Tux application.
    It creates an instance of the TuxApp class.

    Parameters
    ----------
    debug : bool, optional
        Whether to enable debug mode (default is False).

    Returns
    -------
    int
        Exit code: 0 for success, non-zero for failure

    Notes
    -----
    Logging is configured by the CLI script before this is called.
    """
    try:
        if debug:
            logger.info("Starting Tux in debug mode...")
        else:
            logger.info("Starting Tux...")

        app = TuxApp()
        return app.run()

    except (
        TuxDatabaseError,
        TuxSetupError,
        TuxGracefulShutdown,
        TuxError,
        RuntimeError,
        SystemExit,
        KeyboardInterrupt,
        Exception,
    ) as e:
        if isinstance(e, TuxDatabaseError):
            logger.error("Database connection failed")
            logger.info("To start the database, run: docker compose up")
        elif isinstance(e, TuxSetupError):
            logger.error(f"Bot setup failed: {e}")
        elif isinstance(e, TuxGracefulShutdown):
            logger.info(f"Bot shut down gracefully: {e}")
            return 0
        elif isinstance(e, TuxError):
            logger.error(f"Bot error: {e}")
        elif isinstance(e, SystemExit):
            return int(e.code) if e.code is not None else 1
        elif isinstance(e, KeyboardInterrupt):
            logger.info("Shutdown requested by user")
            return 0
        elif isinstance(e, RuntimeError):
            logger.critical(f"Runtime error: {e}")
        else:
            logger.opt(exception=True).critical(f"Application failed to start: {e}")

        return 1
