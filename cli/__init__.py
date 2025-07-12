"""Command-line interface for Tux development tools.

This module provides a modern command-line interface using Click.
"""

# Import cli and main directly from core
from cli.core import cli, main

__all__ = ["cli", "main"]
