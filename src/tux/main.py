import sys

from loguru import logger

from tux.core.app import TuxApp
from tux.services.logger import setup_logging

setup_logging()


def run() -> int:
    """
    Instantiate and run the Tux application.

    This function is the entry point for the Tux application.
    It creates an instance of the TuxApp class.

    Returns
    -------
    int
        Exit code: 0 for success, non-zero for failure
    """

    try:
        logger.info("🚀 Starting Tux...")

        app = TuxApp()
        app.run()

    except RuntimeError as e:
        # Handle setup failures (database, container, etc.)
        if "setup failed" in str(e).lower():
            # Error already logged in setup method, just return failure
            logger.error("❌ Bot startup failed")
            return 1
        logger.critical(f"❌ Application failed to start: {e}")
        return 1

    except SystemExit as e:
        # Handle SystemExit from bot setup failures
        return e.code

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        return 0

    except Exception as e:
        logger.critical(f"Application failed to start: {e}")
        return 1

    else:
        return 0


if __name__ == "__main__":
    exit_code = run()
    sys.exit(exit_code)
