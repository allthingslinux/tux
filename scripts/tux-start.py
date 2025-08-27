#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

from tux.main import run


def main():
    """Start the Tux bot."""
    logger.info("🚀 Starting Tux Discord bot...")

    # Set environment mode
    mode = os.getenv("MODE", "dev")
    os.environ["MODE"] = mode
    logger.info(f"Running in {mode} mode")

    try:
        result = run()
        exit_code = 0 if result is None else result
        if exit_code == 0:
            logger.success("✅ Bot started successfully")
        else:
            logger.error(f"❌ Bot exited with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
