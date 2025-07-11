"""Permission checking utilities for command access control.

This module provides utilities for checking and managing command permission levels
in both traditional prefix commands and slash commands.

Permission Levels
-----------------
The permission system uses numeric levels from 0 to 9, each with an associated role:

0. Member (default)
1. Support
2. Junior Moderator
3. Moderator
4. Senior Moderator
5. Administrator
6. Head Administrator
7. Server Owner
8. Sys Admin
9. Bot Owner
"""

from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import discord
from bot import Tux
from database.controllers import DatabaseController
from discord import app_commands
from discord.ext import commands
from loguru import logger
from utils.config import CONFIG
from utils.exceptions import AppCommandPermissionLevelError, PermissionLevelError

db = DatabaseController().guild_config

T = TypeVar("T", bound=commands.Context[Tux] | discord.Interaction)


async def fetch_guild_config(guild_id: int) -> dict[str, Any]:
    """Fetch all relevant guild config data in a single DB call.

    Parameters
    ----------
    guild_id : int
        The Discord guild ID to fetch configuration for.

    Returns
    -------
    dict[str, Any]
        Dictionary mapping permission level role keys to their corresponding role IDs.
        Keys are in format 'perm_level_{i}_role_id' where i ranges from 0 to 7.
    """
    config = await db.get_guild_config(guild_id)
    return {f"perm_level_{i}_role_id": getattr(config, f"perm_level_{i}_role_id", None) for i in range(8)}


async def has_permission(
    source: commands.Context[Tux] | discord.Interaction,
    lower_bound: int,
    higher_bound: int | None = None,
) -> bool:
    """Check if the source has the required permission level.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction
        The context or interaction to check permissions for.
    lower_bound : int
        The minimum permission level required.
    higher_bound : int | None, optional
        The maximum permission level to check up to, by default None.
        If None, only checks for exact match with lower_bound.

    Returns
    -------
    bool
        True if the user has the required permission level, False otherwise.

    Notes
    -----
    - Permission level 8 is reserved for system administrators
    - Permission level 9 is reserved for the bot owner
    - In DMs, only permission level 0 commands are allowed
    """
    higher_bound = higher_bound or lower_bound

    if source.guild is None:
        return lower_bound == 0

    author = source.author if isinstance(source, commands.Context) else source.user
    guild_config = await fetch_guild_config(source.guild.id)

    roles = [guild_config[f"perm_level_{i}_role_id"] for i in range(lower_bound, min(higher_bound + 1, 8))]
    roles = [role for role in roles if role is not None]

    if isinstance(author, discord.Member) and any(role in [r.id for r in author.roles] for role in roles):
        return True

    return (8 in range(lower_bound, higher_bound + 1) and author.id in CONFIG.SYSADMIN_IDS) or (
        9 in range(lower_bound, higher_bound + 1) and author.id == CONFIG.BOT_OWNER_ID
    )


async def level_to_name(
    source: commands.Context[Tux] | discord.Interaction,
    level: int,
    or_higher: bool = False,
) -> str:
    """Get the name of the permission level.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction
        The context or interaction to get the role name from.
    level : int
        The permission level to get the name for.
    or_higher : bool, optional
        Whether to append "or higher" to the role name, by default False.

    Returns
    -------
    str
        The name of the permission level, either from the guild's role
        or from the default names if no role is set.

    Notes
    -----
    Special levels 8 and 9 always return "Sys Admin" and "Bot Owner" respectively,
    regardless of guild configuration.
    """
    if level in {8, 9}:
        return "Sys Admin" if level == 8 else "Bot Owner"

    assert source.guild

    guild_config = await fetch_guild_config(source.guild.id)
    role_id = guild_config.get(f"perm_level_{level}_role_id")

    if role_id and (role := source.guild.get_role(role_id)):
        return f"{role.name} or higher" if or_higher else role.name

    default_names = {
        0: "Member",
        1: "Support",
        2: "Junior Moderator",
        3: "Moderator",
        4: "Senior Moderator",
        5: "Administrator",
        6: "Head Administrator",
        7: "Server Owner",
        8: "Sys Admin",
        9: "Bot Owner",
    }

    return f"{default_names[level]} or higher" if or_higher else default_names[level]


def permission_check(
    level: int,
    or_higher: bool = True,
) -> Callable[[commands.Context[Tux] | discord.Interaction], Coroutine[Any, Any, bool]]:
    """Generic permission check for both prefix and slash commands.

    Parameters
    ----------
    level : int
        The minimum permission level required.
    or_higher : bool, optional
        Whether to allow higher permission levels, by default True.

    Returns
    -------
    Callable[[commands.Context[Tux] | discord.Interaction], Coroutine[Any, Any, bool]]
        A coroutine function that checks the permission level.

    Raises
    ------
    PermissionLevelError | AppCommandPermissionLevelError
        If the user doesn't have the required permission level.
    """

    async def predicate(ctx: commands.Context[Tux] | discord.Interaction) -> bool:
        """
        Check if the user has the required permission level.

        Parameters
        ----------
        ctx : commands.Context[Tux] | discord.Interaction
            The context or interaction to check permissions for.

        Returns
        -------
        bool
            True if the user has the required permission level, False otherwise.
        """

        if not await has_permission(ctx, level, 9 if or_higher else None):
            name = await level_to_name(ctx, level, or_higher)
            logger.info(
                f"{ctx.author if isinstance(ctx, commands.Context) else ctx.user} tried to run a command without perms. Command: {ctx.command}, Perm Level: {level} or higher: {or_higher}",
            )
            raise (PermissionLevelError if isinstance(ctx, commands.Context) else AppCommandPermissionLevelError)(name)

        return True

    return predicate


def has_pl(level: int, or_higher: bool = True):
    """Check for traditional "prefix" commands.

    Parameters
    ----------
    level : int
        The minimum permission level required.
    or_higher : bool, optional
        Whether to allow higher permission levels, by default True.

    Returns
    -------
    Callable
        A command check that verifies the user's permission level.

    Raises
    ------
    PermissionLevelError
        If used with an Interaction instead of Context.
    """

    async def wrapper(ctx: commands.Context[Tux]) -> bool:
        """
        Check if the user has the required permission level.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context to check permissions for.

        Returns
        -------
        bool
            True if the user has the required permission level, False otherwise.
        """

        if isinstance(ctx, discord.Interaction):
            msg = "Incorrect checks decorator used. Please use ac_has_pl instead and report this as an issue."
            raise PermissionLevelError(msg)
        return await permission_check(level, or_higher)(ctx)

    return commands.check(wrapper)


def ac_has_pl(level: int, or_higher: bool = True):
    """Check for application "slash" commands.

    Parameters
    ----------
    level : int
        The minimum permission level required.
    or_higher : bool, optional
        Whether to allow higher permission levels, by default True.

    Returns
    -------
    Callable
        An application command check that verifies the user's permission level.

    Raises
    ------
    AppCommandPermissionLevelError
        If used with a Context instead of Interaction.
    """

    async def wrapper(interaction: discord.Interaction) -> bool:
        """
        Check if the user has the required permission level.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction to check permissions for.

        Returns
        -------
        bool
            True if the user has the required permission level, False otherwise.
        """
        if isinstance(interaction, commands.Context):
            msg = "Incorrect checks decorator used. Please use has_pl instead and report this as an issue."
            raise AppCommandPermissionLevelError(msg)
        return await permission_check(level, or_higher)(interaction)

    return app_commands.check(wrapper)
