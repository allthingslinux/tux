from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.utils.constants import CONST
from tux.utils.exceptions import AppCommandPermissionLevelError, PermissionLevelError

db = DatabaseController().guild_config


async def has_permission(
    source: commands.Context[Tux] | discord.Interaction,
    lower_bound: int,
    higher_bound: int | None = None,
) -> bool:
    """
    Check if the source has the required permission level.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction
        The source of the command.
    lower_bound : int
        The lower bound of the permission level.
    higher_bound : int | None, optional
        The higher bound of the permission level, by default None.

    Returns
    -------
    bool
        Whether the source has the required permission level.
    """

    higher_bound = higher_bound or lower_bound

    if source.guild is None:
        logger.debug("Guild is None, returning False if lower bound is not 0")
        return lower_bound == 0

    ctx = source if isinstance(source, commands.Context) else None
    interaction = source if isinstance(source, discord.Interaction) else None

    roles = await get_roles_for_bounds(source, lower_bound, higher_bound)

    try:
        author = await get_author_from_source(ctx, interaction)

        if author and any(role.id in roles for role in author.roles):
            return True

    except Exception as e:
        logger.error(f"Exception in permission check: {e}")

    return await check_sysadmin_or_owner(ctx, interaction, lower_bound, higher_bound)


async def get_roles_for_bounds(
    source: Any,
    lower_bound: int,
    higher_bound: int,
) -> list[int]:
    """
    Get the roles for the given bounds.

    Parameters
    ----------
    source : Any
        The source of the command.
    lower_bound : int
        The lower bound of the permission level.
    higher_bound : int
        The higher bound of the permission level.

    Returns
    -------
    list[int]
        The list of role IDs for the given bounds.
    """

    roles: list[Any] = []

    try:
        if higher_bound == lower_bound:
            role_id = await get_perm_level_role_id(source, f"perm_level_{lower_bound}_role_id")

            if role_id:
                roles.append(role_id)
            else:
                logger.debug(f"No Role ID fetched for perm_level_{lower_bound}_role_id")

        else:
            fetched_roles = await get_perm_level_roles(source, lower_bound)
            roles.extend(fetched_roles or [])

    except Exception as e:
        logger.error(f"Error fetching roles: {e}")

    return roles


async def get_author_from_source(
    ctx: Any,
    interaction: Any,
) -> Any:
    """
    Get the author from the source.

    Parameters
    ----------
    ctx : Any
        The context of the command.
    interaction : Any
        The interaction of the command.

    Returns
    -------
    Any
        The author of the command.
    """

    try:
        if ctx and ctx.guild:
            return await ctx.guild.fetch_member(ctx.author.id)

        if interaction and interaction.guild:
            return await interaction.guild.fetch_member(interaction.user.id)

    except Exception as e:
        logger.error(f"Error fetching author: {e}")

    return None


async def check_sysadmin_or_owner(
    ctx: Any,
    interaction: Any,
    lower_bound: int,
    higher_bound: int,
) -> bool:
    """
    Check if the user is a sysadmin or bot owner.

    Parameters
    ----------
    ctx : Any
        The context of the command.
    interaction : Any
        The interaction of the command.
    lower_bound : int
        The lower bound of the permission level.
    higher_bound : int
        The higher bound of the permission level.

    Returns
    -------
    bool
        Whether the user is a sysadmin or bot owner.
    """

    try:
        if ctx:
            user_id = ctx.author.id
        elif interaction:
            user_id = interaction.user.id
        else:
            user_id = None

        if user_id:
            if 8 in range(lower_bound, higher_bound + 1) and user_id in CONST.SYSADMIN_IDS:
                logger.debug("User is a sysadmin")

                return True

            if 9 in range(lower_bound, higher_bound + 1) and user_id == CONST.BOT_OWNER_ID:
                logger.debug("User is the bot owner")

                return True

    except Exception as e:
        logger.error(f"Exception while checking sysadmin or bot owner status: {e}")

    return False


async def level_to_name(
    source: commands.Context[Tux] | discord.Interaction,
    level: int,
    or_higher: bool = False,
) -> str:
    """
    Get the name of the permission level.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction
        The source of the command.
    level : int
        The permission level.
    or_higher : bool, optional
        Whether to include "or higher" in the name, by default False.

    Returns
    -------
    str
        The name of the permission level.
    """

    if level in {8, 9}:
        return "Sys Admin" if level == 8 else "Bot Owner"

    role_name = await get_role_name_from_source(source, level)

    if role_name:
        return f"{role_name} or higher" if or_higher else role_name

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


async def get_role_name_from_source(
    source: Any,
    level: int,
) -> str | None:
    """
    Get the name of the role for the given level from the source.

    Parameters
    ----------
    source : Any
        The source of the command.
    level : int
        The permission level.

    Returns
    -------
    str | None
        The name of the role for the given level.
    """

    role_id = await db.get_perm_level_role(source.guild.id, f"perm_level_{level}_role_id")

    if role_id and (role := source.guild.get_role(role_id)):
        return role.name

    return None


async def get_perm_level_role_id(
    source: commands.Context[Tux] | discord.Interaction,
    level: str,
) -> int | None:
    """
    Get the role ID for the given permission level.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction
        The source of the command.
    level : str
        The permission level.

    Returns
    -------
    int | None
        The role ID for the given permission level or None.
    """

    try:
        guild = source.guild
        return await db.get_perm_level_role(guild.id, level) if guild else None

    except Exception as e:
        logger.error(f"Error retrieving role ID for level {level}: {e}")
        return None


async def get_perm_level_roles(
    source: commands.Context[Tux] | discord.Interaction,
    lower_bound: int,
) -> list[int] | None:
    """
    Get the role IDs for the given permission levels.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction
        The source of the command.
    lower_bound : int
        The lower bound of the permission level.

    Returns
    -------
    list[int] | None
        The role IDs for the given permission levels or None.
    """

    perm_level_roles = {
        0: "perm_level_0_role_id",
        1: "perm_level_1_role_id",
        2: "perm_level_2_role_id",
        3: "perm_level_3_role_id",
        4: "perm_level_4_role_id",
        5: "perm_level_5_role_id",
        6: "perm_level_6_role_id",
        7: "perm_level_7_role_id",
    }

    role_ids: list[Any] = []

    try:
        for level in range(lower_bound, 8):
            if role_field := perm_level_roles.get(level):
                role_id = await db.get_guild_config_field_value(source.guild.id, role_field)  # type: ignore

                if role_id:
                    role_ids.append(role_id)

                else:
                    logger.debug(f"No role ID found for {role_field}, skipping")

    except Exception as e:
        logger.error(f"Error getting perm level roles: {e}")
        return None

    return role_ids


def has_pl(level: int, or_higher: bool = True):
    """
    Check if the source has the required permission level. This is a decorator for traditional "prefix" commands.

    Parameters
    ----------
    level : int
        The permission level required.
    or_higher : bool, optional
        Whether to include "or higher" in the name, by default True.
    """

    async def predicate(ctx: commands.Context[Tux] | discord.Interaction) -> bool:
        if isinstance(ctx, discord.Interaction):
            logger.error("Incorrect checks decorator used. Please use ac_has_pl instead.")
            msg = "Incorrect checks decorator used. Please use ac_has_pl instead and report this as a issue."
            raise PermissionLevelError(msg)

        if not await has_permission(ctx, level, 9 if or_higher else None):
            logger.info(
                f"{ctx.author} tried to run a command without perms. Command: {ctx.command}, Perm Level: {level} or higher: {or_higher}",
            )
            raise PermissionLevelError(await level_to_name(ctx, level, or_higher))

        logger.info(
            f"{ctx.author} ran command {ctx.command} with perm level {await level_to_name(ctx, level, or_higher)}",
        )

        return True

    return commands.check(predicate)


def ac_has_pl(level: int, or_higher: bool = True):
    """
    Check if the source has the required permission level. This is a decorator for application "slash" commands.

    Parameters
    ----------
    level : int
        The permission level required.
    or_higher : bool, optional
        Whether to include "or higher" in the name, by default True.
    """

    async def predicate(ctx: commands.Context[Tux] | discord.Interaction) -> bool:
        if isinstance(ctx, commands.Context):
            logger.error("Incorrect checks decorator used. Please use has_pl instead.")
            msg = "Incorrect checks decorator used. Please use has_pl instead and report this as a issue."
            raise AppCommandPermissionLevelError(msg)

        if not await has_permission(ctx, level, 9 if or_higher else None):
            logger.info(
                f"{ctx.user} tried to run a command without perms. Command: {ctx.command}, Perm Level: {level} or higher: {or_higher}",
            )
            raise AppCommandPermissionLevelError(await level_to_name(ctx, level, or_higher))

        logger.info(
            f"{ctx.user} ran command {ctx.command} with perm level {await level_to_name(ctx, level, or_higher)}",
        )

        return True

    return app_commands.check(predicate)
