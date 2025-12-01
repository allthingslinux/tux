"""Core module for Tux bot.

This module provides the core infrastructure including:
- Main bot class (Tux)
- Base cog class for extensions
- Command prefix resolution
- Permission system and decorators
- Common converters and utilities
"""

from tux.core.app import TuxApp, get_prefix
from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.converters import get_channel_safe
from tux.core.permission_system import DEFAULT_RANKS, get_permission_system

__all__ = [
    # Core classes
    "BaseCog",
    "Tux",
    "TuxApp",
    # Functions
    "get_prefix",
    "get_channel_safe",
    # Permission system
    "requires_command_permission",
    "get_permission_system",
    "DEFAULT_RANKS",
]
