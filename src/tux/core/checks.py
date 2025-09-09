"""
Permission checking utilities for command access control.

This module provides backward compatibility for the permission system.
All functionality has been migrated to tux.services.moderation.condition_checker.

Permission Levels
-----------------
The permission system uses numeric levels from 0 to 8, each with an associated role:

0. Member (default)
1. Trusted
2. Junior Moderator
3. Moderator
4. Senior Moderator
5. Administrator
6. Head Administrator
7. Server Owner
8. Bot Owner (system-level)
"""

# Re-export from the core permission system
from tux.core.permission_system import (
    PermissionLevel,
    get_permission_system,
    init_permission_system,
)
from tux.services.moderation.condition_checker import (
    ConditionChecker,
    require_admin,
    require_bot_owner,
    require_head_admin,
    require_junior_mod,
    # Semantic decorators - DYNAMIC & CONFIGURABLE
    require_member,
    require_moderator,
    require_owner,
    require_senior_mod,
    require_trusted,
)

__all__ = [
    # Classes
    "ConditionChecker",
    "PermissionLevel",
    # Core functions
    "get_permission_system",
    "init_permission_system",
    # Semantic decorators - DYNAMIC & CONFIGURABLE (RECOMMENDED)
    "require_admin",
    "require_bot_owner",
    "require_head_admin",
    "require_junior_mod",
    "require_member",
    "require_moderator",
    "require_owner",
    "require_senior_mod",
    "require_trusted",
]
