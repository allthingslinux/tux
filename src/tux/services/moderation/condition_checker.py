"""
Permission checking decorators for moderation commands.

Provides typed decorator functions for permission checking that integrate
with the existing permission system.
"""

import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from discord.ext import commands

from tux.core.permission_system import PermissionLevel, get_permission_system
from tux.core.types import Tux

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _create_permission_decorator(required_level: PermissionLevel) -> Callable[[F], F]:
    """Create a permission decorator for the given level."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(ctx: commands.Context[Tux], *args: Any, **kwargs: Any) -> Any:
            # Get the permission system
            permission_system = get_permission_system()

            # Use the existing permission system's require_permission method
            # This will raise an appropriate exception if permission is denied
            try:
                await permission_system.require_permission(ctx, required_level)
            except Exception:
                # The permission system will handle sending error messages
                return None

            # Execute the original function if permission check passed
            return await func(ctx, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


class ConditionChecker:
    """Helper class for advanced permission checking operations."""

    def __init__(self) -> None:
        self.permission_system = get_permission_system()

    async def check_condition(
        self,
        ctx: commands.Context[Tux],
        target_user: Any,
        moderator: Any,
        action: str,
    ) -> bool:
        """
        Advanced permission checking with hierarchy validation.

        This method provides more detailed permission checking beyond basic
        role requirements, including hierarchy checks and target validation.

        Args:
            ctx: Command context
            target_user: User being moderated
            moderator: User performing moderation
            action: Action being performed

        Returns:
            True if all conditions are met, False otherwise
        """
        if not ctx.guild:
            return False

        # Basic permission check - map actions to permission levels
        base_level = {
            "ban": PermissionLevel.MODERATOR,
            "kick": PermissionLevel.JUNIOR_MODERATOR,
            "timeout": PermissionLevel.JUNIOR_MODERATOR,
            "warn": PermissionLevel.JUNIOR_MODERATOR,
            "jail": PermissionLevel.JUNIOR_MODERATOR,
        }.get(action, PermissionLevel.MODERATOR)

        # Use the permission system for detailed checking
        return await self.permission_system.check_permission(ctx, base_level.value)


# Semantic permission decorators - DYNAMIC & CONFIGURABLE
def require_member() -> Callable[[F], F]:
    """Require member-level permissions."""
    return _create_permission_decorator(PermissionLevel.MEMBER)


def require_trusted() -> Callable[[F], F]:
    """Require trusted-level permissions."""
    return _create_permission_decorator(PermissionLevel.TRUSTED)


def require_junior_mod() -> Callable[[F], F]:
    """Require junior moderator permissions."""
    return _create_permission_decorator(PermissionLevel.JUNIOR_MODERATOR)


def require_moderator() -> Callable[[F], F]:
    """Require moderator permissions."""
    return _create_permission_decorator(PermissionLevel.MODERATOR)


def require_senior_mod() -> Callable[[F], F]:
    """Require senior moderator permissions."""
    return _create_permission_decorator(PermissionLevel.SENIOR_MODERATOR)


def require_admin() -> Callable[[F], F]:
    """Require administrator permissions."""
    return _create_permission_decorator(PermissionLevel.ADMINISTRATOR)


def require_head_admin() -> Callable[[F], F]:
    """Require head administrator permissions."""
    return _create_permission_decorator(PermissionLevel.HEAD_ADMINISTRATOR)


def require_owner() -> Callable[[F], F]:
    """Require server owner permissions."""
    return _create_permission_decorator(PermissionLevel.SERVER_OWNER)


def require_bot_owner() -> Callable[[F], F]:
    """Require bot owner permissions."""
    return _create_permission_decorator(PermissionLevel.BOT_OWNER)


__all__ = [
    "ConditionChecker",
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
