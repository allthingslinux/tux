"""Tux - The all in one discord bot for the All Things Linux Community.

This package provides a comprehensive Discord bot with modular architecture,
extensive functionality, and professional development practices.
"""

# Import the unified version system
from tux.shared.version import get_version

# Module-level version constant
# Uses the unified version system for consistency
__version__: str = get_version()
