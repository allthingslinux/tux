"""Core module for Tux bot.

This module provides the core infrastructure including:
- Base cog class for extensions
- Database service for data persistence
"""

from tux.core.base_cog import BaseCog
from tux.database.service import DatabaseService

__all__ = [
    "BaseCog",
    "DatabaseService",
]
