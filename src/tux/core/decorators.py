"""Dynamic permission decorators with database-driven access control.

This module provides database-driven permission decorators that read required
permission ranks from the database per-guild. All commands use
@requires_command_permission() with no arguments. The required permission rank
is stored in the database per-guild. Guilds must configure permissions before
commands work (safe default). Without configuration, commands are denied by
default.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

import discord
from discord.ext import commands
from loguru import logger

from tux.core.permission_system import PermissionSystem, get_permission_system
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxPermissionDeniedError

__all__ = ["requires_command_permission"]

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def requires_command_permission(
    *,
    allow_unconfigured: bool = False,
) -> Callable[[F], F]:
    """
    Provide dynamic, database-driven command permissions.

    This decorator provides fully dynamic permission checking that reads
    required permission ranks from the database per guild. Commands are
    denied by default if not configured (safe mode).

    For group commands with subcommands, if a subcommand is not configured,
    the system will fall back to checking parent commands. For example:
    - "config ranks init" checks: "config ranks init" -> "config ranks" -> "config"
    - "cases search" checks: "cases search" -> "cases"

    This allows configuring a parent group command (e.g., "config") to protect
    all subcommands, while still allowing per-subcommand overrides.

    Parameters
    ----------
    allow_unconfigured : bool, optional
        If True, allow commands without database configuration.
        If False (default), deny unconfigured commands.

    Returns
    -------
    Callable[[F], F]
        The decorated function with permission checking.
    """

    def decorator(func: F) -> F:
        """Apply permission checking wrapper to the decorated function.

        Parameters
        ----------
        func : F
            The function to be decorated with permission checking.

        Returns
        -------
        F
            The wrapped function with permission checking.
        """

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Check permissions and execute the decorated function if allowed.

            Performs comprehensive permission checking including bot owner bypass,
            guild owner bypass, and database-driven rank checking.

            Parameters
            ----------
            *args : Any
                Positional arguments passed to the decorated function.
            **kwargs : Any
                Keyword arguments passed to the decorated function.

            Returns
            -------
            Any
                The result of the decorated function execution.

            Raises
            ------
            TuxPermissionDeniedError
                When user lacks required permissions for the command.
            ValueError
                When context or interaction cannot be found in arguments.
            """
            # Extract context or interaction from args
            ctx, interaction = _extract_context_or_interaction(args)

            # Get command name for logging
            command_name = _get_command_name(ctx, interaction, func)

            logger.debug(f"Permission check for command: {command_name}")

            if ctx is None and interaction is None:
                logger.error(
                    "Could not find context or interaction in command arguments",
                )
                error_msg = "Unable to find context or interaction parameter"
                raise ValueError(error_msg)

            # Get guild from context or interaction
            guild = ctx.guild if ctx else interaction.guild if interaction else None

            # Only check in guilds (DMs bypass)
            if not guild:
                return await func(*args, **kwargs)

            # Get user ID
            user_id = (
                ctx.author.id if ctx else interaction.user.id if interaction else 0
            )

            # Check bypasses first (bot owner, sysadmin, guild owner)
            if _should_bypass_permission_check(user_id, guild, command_name):
                return await func(*args, **kwargs)

            # Perform permission check with timing
            await _check_permissions(
                ctx,
                interaction,
                guild,
                user_id,
                command_name,
                allow_unconfigured,
            )

            # Permission check passed, execute command
            return await func(*args, **kwargs)

        # Mark as using dynamic permissions
        wrapper.__uses_dynamic_permissions__ = True  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator


def _get_command_name(
    ctx: commands.Context[Any] | None,
    interaction: discord.Interaction[Any] | None,
    func: Callable[..., Any],
) -> str:
    """Extract command name from context, interaction, or function."""
    if ctx and ctx.command:
        return ctx.command.qualified_name
    if interaction and interaction.command:
        return interaction.command.qualified_name
    return func.__name__


def _should_bypass_permission_check(
    user_id: int,
    guild: discord.Guild | None,
    command_name: str,
) -> bool:
    """Check if user should bypass permission checks (bot owner, sysadmin, guild owner)."""
    # Bot owners and sysadmins bypass ALL permission checks
    if user_id == CONFIG.USER_IDS.BOT_OWNER_ID or user_id in CONFIG.USER_IDS.SYSADMINS:
        logger.debug(
            f"Bot owner/sysadmin {user_id} bypassing permission check for '{command_name}'",
        )
        return True

    # Guild/Server owner bypass
    if guild and guild.owner_id == user_id:
        logger.debug(
            f"Guild owner {user_id} bypassing permission check for '{command_name}'",
        )
        return True

    return False


async def _check_permissions(
    ctx: commands.Context[Any] | None,
    interaction: discord.Interaction[Any] | None,
    guild: discord.Guild,
    user_id: int,
    command_name: str,
    allow_unconfigured: bool,
) -> None:
    """Perform permission check with timing and logging."""
    permission_system = get_permission_system()

    # Start timing permission check
    check_start = time.perf_counter()

    # Get command permission config from database
    cmd_perm_start = time.perf_counter()
    cmd_perm = await permission_system.get_command_permission(
        guild.id,
        command_name,
    )
    cmd_perm_time = (time.perf_counter() - cmd_perm_start) * 1000

    # If not configured, check if we should allow or deny
    if cmd_perm is None:
        if not allow_unconfigured:
            total_time = (time.perf_counter() - check_start) * 1000
            logger.debug(
                f"Permission check denied (unconfigured) for '{command_name}' "
                f"(guild {guild.id}, user {user_id}) - "
                f"cmd_perm: {cmd_perm_time:.2f}ms, total: {total_time:.2f}ms",
            )
            raise TuxPermissionDeniedError(
                required_rank=0,
                user_rank=0,
                command_name=command_name,
            )
        # Allow unconfigured commands
        total_time = (time.perf_counter() - check_start) * 1000
        logger.debug(
            f"Permission check passed (unconfigured allowed) for '{command_name}' "
            f"(guild {guild.id}, user {user_id}) - "
            f"cmd_perm: {cmd_perm_time:.2f}ms, total: {total_time:.2f}ms",
        )
        return

    # Get user's permission rank
    user_rank_start = time.perf_counter()
    if ctx:
        user_rank = await permission_system.get_user_permission_rank(ctx)
    elif interaction:
        user_rank = await _get_user_rank_from_interaction(
            permission_system,
            interaction,
        )
    else:
        user_rank = 0
    user_rank_time = (time.perf_counter() - user_rank_start) * 1000

    # Check if user meets required rank
    if user_rank < cmd_perm.required_rank:
        total_time = (time.perf_counter() - check_start) * 1000
        logger.debug(
            f"Permission check denied for '{command_name}' "
            f"(guild {guild.id}, user {user_id}) - "
            f"required: {cmd_perm.required_rank}, user: {user_rank} - "
            f"cmd_perm: {cmd_perm_time:.2f}ms, user_rank: {user_rank_time:.2f}ms, "
            f"total: {total_time:.2f}ms",
        )
        raise TuxPermissionDeniedError(
            cmd_perm.required_rank,
            user_rank,
            command_name,
        )

    # Permission check passed
    total_time = (time.perf_counter() - check_start) * 1000
    logger.debug(
        f"Permission check passed for '{command_name}' "
        f"(guild {guild.id}, user {user_id}, rank {user_rank}) - "
        f"cmd_perm: {cmd_perm_time:.2f}ms, user_rank: {user_rank_time:.2f}ms, "
        f"total: {total_time:.2f}ms",
    )


async def _get_user_rank_from_interaction(
    permission_system: PermissionSystem,
    interaction: discord.Interaction[Any],
) -> int:
    """
    Get user permission rank from an interaction (for app commands).

    Uses discord.py's built-in Context.from_interaction() to create a proper
    context, then queries the permission system for the user's rank.

    Parameters
    ----------
    permission_system : PermissionSystem
        The permission system to use.
    interaction : discord.Interaction[Any]
        The interaction to get the user permission rank from.

    Returns
    -------
    int
        The user permission rank.
    """
    ctx: commands.Context[Any] = await commands.Context.from_interaction(interaction)  # type: ignore[reportUnknownMemberType]

    return await permission_system.get_user_permission_rank(ctx)


def _extract_context_or_interaction(
    args: tuple[Any, ...],
) -> tuple[commands.Context[Any] | None, discord.Interaction[Any] | None]:
    """
    Extract Discord context or interaction from function arguments.

    Searches through positional arguments to find a commands.Context or
    discord.Interaction instance. Handles hybrid commands that may have both.

    Parameters
    ----------
    args : tuple[Any, ...]
        The positional arguments to search through.

    Returns
    -------
    tuple[commands.Context[Any] | None, discord.Interaction[Any] | None]
        Tuple of (context, interaction). One will be None, the other populated.
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
            return (
                cast(commands.Context[Any], arg),
                cast(discord.Interaction[Any], arg.interaction),
            )
        if hasattr(arg, "bot") and hasattr(arg, "guild"):
            # Likely a context-like object
            return (cast(commands.Context[Any], arg), None)
    return (None, None)
