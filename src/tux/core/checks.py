"""
Dynamic Permission System - Fully Database-Driven

This module provides dynamic permission decorators with ZERO hardcoded opinions.
All permission requirements are stored in the database and configured per-guild.

Usage:
    @requires_command_permission()  # 100% dynamic, reads from database
    async def ban(self, ctx, user): ...

Configuration:
    Guilds configure permissions via /config permission commands.
    Without configuration, commands are denied by default (secure).
"""

# Dynamic permission decorator
from tux.core.decorators import requires_command_permission

# Core permission system functions
from tux.core.permission_system import (
    get_permission_system,
    init_permission_system,
)

# Permission exceptions
from tux.shared.exceptions import TuxPermissionDeniedError

__all__ = [
    # Exceptions
    "TuxPermissionDeniedError",
    # Core functions
    "get_permission_system",
    "init_permission_system",
    # The ONLY decorator - 100% dynamic
    "requires_command_permission",
]
