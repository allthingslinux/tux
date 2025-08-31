#!/usr/bin/env python3
"""
Command Line Interface for Tux Discord Bot.

This module provides the CLI entry point for running the bot.
"""

import sys

from tux.main import run


def main():
    """Entry point for the Tux CLI."""
    sys.exit(run())


if __name__ == "__main__":
    main()
