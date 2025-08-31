#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and initialize the custom Tux logger
import logger_setup  # noqa: F401 # pyright: ignore[reportUnusedImport]
from loguru import logger

from tux.main import run


def main():
    """Start the Tux bot."""
    logger.info("🚀 Starting Tux Discord bot...")

    logger.info("Starting Tux Discord bot...")

    try:
        exit_code = run()
        if exit_code == 0:
            logger.success("✅ Bot started successfully")
        else:
            logger.error(f"❌ Bot exited with code {exit_code}")
        sys.exit(exit_code)
    except RuntimeError as e:
        # Handle setup failures (database, container, etc.)
        if "setup failed" in str(e).lower():
            # Error already logged in setup method, just exit
            sys.exit(1)
        elif "Event loop stopped before Future completed" in str(e):
            logger.info("🛑 Bot shutdown completed")
            sys.exit(0)
        else:
            logger.error(f"❌ Runtime error: {e}")
            sys.exit(1)
    except SystemExit as e:
        # Bot failed during startup, exit with the proper code
        # Don't log additional error messages since they're already handled
        sys.exit(e.code)
    except KeyboardInterrupt:
        logger.info("🛑 Bot shutdown requested by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
