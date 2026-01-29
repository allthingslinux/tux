"""Dynamic permission decorators with database-driven access control.

This module provides database-driven permission decorators that read required
permission ranks from the database per-guild. All commands use
@requires_command_permission() with no arguments. The required permission rank
is stored in the database per-guild. Guilds must configure permissions before
commands work (safe default). Without configuration, commands are denied by
default.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

import discord
from discord.ext import commands
from loguru import logger

from tux.core.permission_system import PermissionSystem, get_permission_system
from tux.database.models import PermissionCommand
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxPermissionDeniedError

__all__ = ["requires_command_permission", "command_permission_check"]

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _get_param_value(
    func: Callable[..., Any],
    param_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Get the value of a parameter by name from the given args/kwargs."""
    sig = inspect.signature(func)
    params = list(sig.parameters)
    if param_name not in params:
        return None
    index = params.index(param_name)
    return args[index] if index < len(args) else kwargs.get(param_name)


def requires_command_permission(
    *,
    allow_unconfigured: bool = False,
    allow_self_use_for_param: str | None = None,
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
    allow_self_use_for_param : str | None, optional
        If set, skip the permission check when the argument with this name
        (e.g. ``"member"``) refers to the invoker (invoker id == target id).

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

            When the command uses check-phase permission (no allow_self_use_for_param),
            permission was already enforced before argument conversion; this wrapper
            then just invokes the callback.
            """
            # Permission already run in check phase (before conversion) for this command
            if getattr(wrapper, "__tux_perm_check_in_phase__", False):
                return await func(*args, **kwargs)
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

            # Allow self-use when target param is the invoker (e.g. clearafk on self)
            if allow_self_use_for_param and guild:
                target = _get_param_value(func, allow_self_use_for_param, args, kwargs)
                if target is not None and getattr(target, "id", None) == user_id:
                    logger.debug(
                        f"Permission check skipped (self-use) for '{_get_command_name(ctx, interaction, func)}' "
                        f"(guild {guild.id}, user {user_id})",
                    )
                    return await func(*args, **kwargs)

            # For slash commands, defer early to prevent timeout during permission check
            # This acknowledges the interaction before the potentially slow permission check
            if interaction and not interaction.response.is_done():
                try:
                    await interaction.response.defer(ephemeral=True)
                    logger.trace(
                        f"Deferred interaction early for command: {command_name}",
                    )
                except Exception as e:
                    # If defer fails (already responded, etc.), continue anyway
                    logger.debug(f"Could not defer interaction for {command_name}: {e}")

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

        # Mark as using dynamic permissions; store options for check-phase registration
        wrapper.__uses_dynamic_permissions__ = True  # type: ignore[attr-defined]
        wrapper.__tux_perm_allow_unconfigured__ = allow_unconfigured  # type: ignore[attr-defined]
        wrapper.__tux_perm_allow_self_use_for_param__ = allow_self_use_for_param  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator


async def command_permission_check(ctx: commands.Context[Any]) -> bool:
    """
    Run permission check in the command check phase (before argument conversion).

    Used for commands that do not use allow_self_use_for_param so users get
    "permission denied" before "missing required argument". Reads allow_unconfigured
    from ctx.command.callback.__tux_perm_allow_unconfigured__.
    """
    # Defer slash interactions before potentially slow permission check
    inter = getattr(ctx, "interaction", None)
    if inter is not None and not inter.response.is_done():
        with contextlib.suppress(Exception):
            await inter.response.defer(ephemeral=True)
    if not ctx.guild or not ctx.command:
        return True
    # Bot owner, sysadmin, and guild owner bypass (same as callback wrapper path)
    if _should_bypass_permission_check(
        ctx.author.id,
        ctx.guild,
        ctx.command.qualified_name,
    ):
        return True
    callback = getattr(ctx.command, "callback", None)
    allow_unconfigured = getattr(callback, "__tux_perm_allow_unconfigured__", False)
    await _check_permissions(
        ctx,
        getattr(ctx, "interaction", None),
        ctx.guild,
        ctx.author.id,
        ctx.command.qualified_name,
        allow_unconfigured,
    )
    return True


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

    # Run command permission and user rank lookups in parallel since they're independent
    # This can significantly reduce total time when both need database queries.
    # Race condition safety: Both operations are read-only, use separate cache keys,
    # and use separate database sessions, so parallel execution is safe.
    cmd_perm_task = permission_system.get_command_permission(guild.id, command_name)

    # Prepare user rank lookup task
    if ctx:
        user_rank_task = permission_system.get_user_permission_rank(ctx)
    elif interaction:
        user_rank_task = _get_user_rank_from_interaction(
            permission_system,
            interaction,
        )
    else:
        user_rank_task = None

    # Execute both lookups in parallel
    cmd_perm_start = time.perf_counter()
    if user_rank_task is not None:
        gathered = await asyncio.gather(
            cmd_perm_task,
            user_rank_task,
            return_exceptions=False,
        )
        cmd_perm: PermissionCommand | None = gathered[0]
        user_rank: int = gathered[1]
    else:
        cmd_perm = await cmd_perm_task
        user_rank = 0
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

    # Check if user meets required rank
    if user_rank < cmd_perm.required_rank:
        total_time = (time.perf_counter() - check_start) * 1000
        logger.debug(
            f"Permission check denied for '{command_name}' "
            f"(guild {guild.id}, user {user_id}) - "
            f"required: {cmd_perm.required_rank}, user: {user_rank} - "
            f"cmd_perm: {cmd_perm_time:.2f}ms (parallel), total: {total_time:.2f}ms",
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
        f"cmd_perm: {cmd_perm_time:.2f}ms (parallel), total: {total_time:.2f}ms",
    )


async def _get_user_rank_from_interaction(
    permission_system: PermissionSystem,
    interaction: discord.Interaction[Any],
) -> int:
    """
    Get user permission rank from an interaction (for app commands).

    Optimized version that extracts roles directly from the interaction
    without creating a slow Context object. This avoids the expensive
    Context.from_interaction() call which can take several seconds.

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
    if not interaction.guild_id:
        return 0

    # Extract user ID
    user_id = interaction.user.id if interaction.user else 0

    # Extract role IDs from member if available, otherwise fetch member
    user_roles: list[int] = []
    if isinstance(interaction.user, discord.Member):
        # Member object already has roles
        user_roles = [role.id for role in interaction.user.roles]
    elif interaction.guild:
        # Try to get member from guild cache (fast)
        member = interaction.guild.get_member(user_id)
        if not member:
            # Fallback: fetch member (slower, but rare)
            # This should be avoided if possible - member should be in cache
            try:
                member = await interaction.guild.fetch_member(user_id)
            except Exception as e:
                logger.debug(
                    f"Could not fetch member {user_id} for permission check: {e}",
                )
                # If we can't get member, return 0 (no permissions)
                return 0
        if member:
            user_roles = [role.id for role in member.roles]

    # Use optimized method that doesn't require Context
    return await permission_system.get_user_permission_rank_from_interaction(
        interaction.guild_id,
        user_id,
        user_roles,
    )


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
