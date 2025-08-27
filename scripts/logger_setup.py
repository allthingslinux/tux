#!/usr/bin/env python3
"""
Logger setup utility for Tux scripts.

This module provides a way for scripts to use the custom Tux logger
without running the full bot application.
"""

import sys
from pathlib import Path

# Add src to path so we can import tux modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from tux.services.logger import setup_logging


def init_tux_logger() -> None:
    """
    Initialize the Tux custom logger for scripts.

    This function sets up the same logging configuration used by the main Tux bot,
    including the custom LoguruRichHandler with Rich formatting.

    Call this function at the start of your script to use the Tux logger.
    """
    setup_logging()


# Auto-initialize when imported
init_tux_logger()
