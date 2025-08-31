#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and initialize the custom Tux logger
import logger_setup  # noqa: F401 # pyright: ignore[reportUnusedImport]
from loguru import logger

from tux import __version__


def main():
    """Show Tux version."""
    logger.info(f"📋 Tux version: {__version__}")


if __name__ == "__main__":
    main()
