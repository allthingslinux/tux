"""
Dynamic Permission Decorators.

This module provides fully dynamic, database-driven permission decorators
that have NO hardcoded opinions about permission ranks or names.

Architecture:
    ALL commands use @requires_command_permission() with NO arguments.
    The required permission rank is stored in the database per-guild.
    Guilds MUST configure permissions before commands work (safe default).

Recommended Usage:
    @requires_command_permission()  # 100% dynamic, reads from database
    async def ban(self, ctx, user): ...

Configuration:
    Admins use `/config permission command ban rank:3` to set requirements.
    Without configuration, commands are DENIED by default (safe mode).
"""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

import discord
from discord.ext import commands
from loguru import logger

from tux.core.permission_system import get_permission_system
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxPermissionDeniedError

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def requires_command_permission(*, allow_unconfigured: bool = False) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: PLR0912
            # Extract context or interaction from args
            ctx, interaction = _extract_context_or_interaction(args)

            if ctx is None and interaction is None:
                logger.error("Could not find context or interaction in command arguments")
                msg = "Unable to find context or interaction parameter"
                raise ValueError(msg)

            # Get guild from context or interaction
            guild = ctx.guild if ctx else (interaction.guild if interaction else None)

            # Only check in guilds (DMs bypass)
            if not guild:
                return await func(*args, **kwargs)

            # Get user ID
            user_id = ctx.author.id if ctx else (interaction.user.id if interaction else 0)

            # Bot owners and sysadmins bypass ALL permission checks
            if user_id == CONFIG.USER_IDS.BOT_OWNER_ID or user_id in CONFIG.USER_IDS.SYSADMINS:
                logger.debug(f"Bot owner/sysadmin {user_id} bypassing permission check")
                return await func(*args, **kwargs)

            # Guild/Server owner bypass
            if guild.owner_id == user_id:
                logger.debug(f"Guild owner {user_id} bypassing permission check")
                return await func(*args, **kwargs)

            # Get permission system (only if not already bypassed)
            permission_system = get_permission_system()

            # Get command name
            if ctx and ctx.command:
                command_name = ctx.command.qualified_name
            elif interaction and interaction.command:
                command_name = interaction.command.qualified_name
            else:
                command_name = func.__name__

            # Get command permission config from database
            cmd_perm = await permission_system.get_command_permission(
                guild.id,
                command_name,
            )

            # If not configured, check if we should allow or deny
            if cmd_perm is None:
                if not allow_unconfigured:
                    # Safe default: deny unconfigured commands
                    raise TuxPermissionDeniedError(
                        required_rank=0,
                        user_rank=0,
                        command_name=command_name,
                    )
                # Allow unconfigured commands
                return await func(*args, **kwargs)

            # Get user's permission rank
            if ctx:
                user_rank = await permission_system.get_user_permission_rank(ctx)
            elif interaction:
                user_rank = await _get_user_rank_from_interaction(permission_system, interaction)
            else:
                user_rank = 0  # Fallback

            # Check if user meets required rank
            if user_rank < cmd_perm.required_rank:
                raise TuxPermissionDeniedError(
                    cmd_perm.required_rank,
                    user_rank,
                    command_name,
                )

            # Permission check passed, execute command
            return await func(*args, **kwargs)

        # Mark as using dynamic permissions
        wrapper.__uses_dynamic_permissions__ = True  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator


async def _get_user_rank_from_interaction(
    permission_system: Any,
    interaction: discord.Interaction[Any],
) -> int:
    """
    Get user permission rank from an interaction (for app commands).

    Uses Discord.py's built-in Context.from_interaction() to create a proper context.
    """
    ctx: commands.Context[Any] = await commands.Context.from_interaction(interaction)  # type: ignore[reportUnknownMemberType]

    return await permission_system.get_user_permission_rank(ctx)


def _extract_context_or_interaction(
    args: tuple[Any, ...],
) -> tuple[commands.Context[Any] | None, discord.Interaction[Any] | None]:
    """
    Extract Discord context or interaction from function arguments.

    Returns
    -------
        Tuple of (context, interaction) - one will be None, the other populated
    """
    for arg in args:
        # Prefix commands use Context
        if isinstance(arg, commands.Context):
            return (cast(commands.Context[Any], arg), None)
        # App commands use Interaction
        if isinstance(arg, discord.Interaction):
            return (None, cast(discord.Interaction[Any], arg))
        # Hybrid commands can be either, check attributes
        if hasattr(arg, "interaction") and arg.interaction:
            # Hybrid command invoked as slash command
            return (cast(commands.Context[Any], arg), cast(discord.Interaction[Any], arg.interaction))
        if hasattr(arg, "bot") and hasattr(arg, "guild"):
            # Likely a context-like object
            return (cast(commands.Context[Any], arg), None)
    return (None, None)


__all__ = [
    "requires_command_permission",
]
