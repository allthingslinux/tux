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


def run(debug: bool = False) -> int:  # noqa: PLR0911
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

    except TuxDatabaseError:
        logger.error("Database connection failed")
        logger.info("To start the database, run: docker compose up")
        return 1
    except TuxSetupError as e:
        logger.error(f"Bot setup failed: {e}")
        return 1
    except TuxGracefulShutdown as e:
        logger.info(f"Bot shut down gracefully: {e}")
        return 0
    except TuxError as e:
        logger.error(f"Bot error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
    except RuntimeError as e:
        logger.critical(f"Runtime error: {e}")
        return 1
    except Exception as e:
        logger.opt(exception=True).critical(f"Application failed to start: {e}")
        return 1
