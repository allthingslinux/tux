"""Refactored help system with separated concerns."""

# Import only what's needed externally to avoid circular imports
from .help import TuxHelp

__all__ = ["TuxHelp"]
