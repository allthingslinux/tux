from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.handlers.error import AppCommandPermissionLevelError, PermissionLevelError
from tux.utils.constants import CONST

db = DatabaseController().guild_config


async def has_permission(
    source: commands.Context[commands.Bot] | discord.Interaction,
    lower_bound: int,
    higher_bound: int | None = None,
) -> bool:
    if higher_bound is None:
        higher_bound = lower_bound

    if source.guild is None:
        logger.debug("Guild is None, returning False if lower bound is not 0")
        return lower_bound == 0

    if isinstance(source, commands.Context):
        logger.debug(f"Checking permissions for context-based command by {source.author}")
        ctx, interaction = source, None
    else:
        logger.debug(f"Checking permissions for interaction-based command by {source.user}")
        interaction, ctx = source, None

    roles: list[Any] = []
    try:
        # Single level and not sysadmin/bot owner
        if higher_bound == lower_bound:
            logger.debug(f"Getting role id for permission level {lower_bound}")
            role_id = await get_perm_level_role_id(source, f"perm_level_{lower_bound}_role_id")
            logger.debug(f"Received role ID {role_id} for level {lower_bound}")
            if role_id:
                roles.append(role_id)
                logger.debug(f"Added role ID {role_id} for permission level {lower_bound}")
            else:
                logger.debug(f"No Role ID fetched for perm_level_{lower_bound}_role_id")

        # Range checks
        else:
            logger.debug(f"Getting role ids for permission levels above and equal to {lower_bound}")
            fetched_roles = await get_perm_level_roles(source, lower_bound)
            logger.debug(f"Roles fetched: {fetched_roles}")
            if fetched_roles:
                roles.extend(fetched_roles)
                logger.debug(f"Added roles {fetched_roles} for levels above and equal to {lower_bound}")
            else:
                logger.debug(f"No roles fetched for levels above and equal to {lower_bound}")

        logger.debug(f"Roles required for level {lower_bound} or higher: {roles}")

        # Fetch author/member roles
        if ctx and ctx.guild:
            author = await ctx.guild.fetch_member(ctx.author.id)
        elif interaction and interaction.guild:
            author = await interaction.guild.fetch_member(interaction.user.id)

        logger.debug(f"Author's roles: {[role.id for role in author.roles]}")

        # Author's role matching
        is_authorized = any(role.id in roles for role in author.roles)
        logger.debug(f"Role matching success: {is_authorized}")

        if is_authorized:
            logger.debug(f"User has permission level {lower_bound} or higher")
            return True

        logger.debug("No matching roles found for user")

    except Exception as e:
        logger.error(f"Exception in permission check: {e}")

    # Fallback Path: Sysadmin/Bot Owner Check
    logger.debug("All checks failed, checking for sysadmin or bot owner status")

    try:
        if ctx:
            if 8 in range(lower_bound, higher_bound + 1) and ctx.author.id in CONST.SYSADMIN_IDS:
                logger.debug("User is a sysadmin")
                return True
            if 9 in range(lower_bound, higher_bound + 1) and ctx.author.id == CONST.BOT_OWNER_ID:
                logger.debug("User is the bot owner")
                return True
        else:
            if interaction and 8 in range(lower_bound, higher_bound + 1) and interaction.user.id in CONST.SYSADMIN_IDS:
                logger.debug("User is a sysadmin")
                return True
            if interaction and 9 in range(lower_bound, higher_bound + 1) and interaction.user.id == CONST.BOT_OWNER_ID:
                logger.debug("User is the bot owner")
                return True
    except Exception as e:
        logger.error(f"Exception while checking sysadmin or bot owner status: {e}")

    logger.debug("All checks failed, returning False")
    return False


async def level_to_name(
    source: commands.Context[commands.Bot] | discord.Interaction,
    level: int,
    or_higher: bool = False,
) -> str:
    """
    Convert a permission level to a name.

    Parameters
    ----------
    level : int
        The permission level to convert.
    or_higher : bool, optional
        Whether the user should have the permission level or higher, by default False

    Returns
    -------
    str
        The name of the permission level.
    """
    if level in {8, 9}:
        return "Sys Admin" if level == 8 else "Bot Owner"

    if isinstance(source, commands.Context):
        ctx = source
        if ctx.guild is None:
            return "Error"
        role_id = await db.get_perm_level_role(ctx.guild.id, f"perm_level_{level}_role_id")
        if role_id and (role := ctx.guild.get_role(role_id)):
            return f"{role.name} or higher" if or_higher else role.name
    else:
        interaction = source
        if not interaction or not interaction.guild:
            return "Error"
        role_id = await db.get_perm_level_role(interaction.guild.id, f"perm_level_{level}_role_id")
        if role_id and (role := interaction.guild.get_role(role_id)):
            return f"{role.name} or higher" if or_higher else role.name

    dictionary = {
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

    return f"{dictionary[level]} or higher" if or_higher else dictionary[level]


async def get_perm_level_role_id(
    source: commands.Context[commands.Bot] | discord.Interaction,
    level: str,
) -> int | None:
    """
    Get the role id of the permission level.
    """
    role_id = None
    try:
        if isinstance(source, commands.Context):
            ctx = source
            if ctx.guild is None:
                return None

            role_id = await db.get_perm_level_role(ctx.guild.id, level)
        else:
            interaction = source
            if not interaction or not interaction.guild:
                return None

            role_id = await db.get_perm_level_role(interaction.guild.id, level)
        logger.debug(f"Role ID retrieved for {level}: {role_id}")
    except Exception as e:
        logger.error(f"Error retrieving role ID for level {level}: {e}")
    return role_id


async def get_perm_level_roles(
    source: commands.Context[commands.Bot] | discord.Interaction,
    lower_bound: int,
) -> list[int] | None:
    """
    Get the role ids of the permission levels between the lower and higher bounds.
    """
    perm_level_roles: dict[int, str] = {
        0: "perm_level_0_role_id",
        1: "perm_level_1_role_id",
        2: "perm_level_2_role_id",
        3: "perm_level_3_role_id",
        4: "perm_level_4_role_id",
        5: "perm_level_5_role_id",
        6: "perm_level_6_role_id",
        7: "perm_level_7_role_id",
    }
    role_ids: list[int] = []

    try:
        logger.debug(f"Starting to fetch roles for levels {lower_bound} to 7")
        for level in range(lower_bound, 8):
            role_field = perm_level_roles.get(level)
            logger.debug(f"Fetching role_id for role_field: {role_field}")
            if role_field:
                role_id = await db.get_guild_config_field_value(source.guild.id, role_field)  # type: ignore
                logger.debug(f"Role ID retrieved for {role_field}: {role_id}")
                if role_id:
                    role_ids.append(role_id)
                else:
                    logger.debug(f"No role ID found for {role_field}, skipping")
        logger.debug(f"Retrieved role_ids: {role_ids}")
    except KeyError as e:
        logger.error(f"Key error when accessing role field: {e}")
    except AttributeError as e:
        logger.error(f"Attribute error, likely due to accessing a wrong attribute: {e}")
    except Exception as e:
        logger.error(f"General error getting perm level roles: {e}")
        return None

    return role_ids


# checks if the user has permission level 1 (Support)
def has_pl(level: int, or_higher: bool = True):
    async def predicate(ctx: commands.Context[commands.Bot] | discord.Interaction) -> bool:
        if isinstance(ctx, discord.Interaction):
            logger.error("Interaction source is not supported for this check, please use ac_has_pl instead.")
            msg = "Interaction source is not supported for this check, please use ac_has_pl instead. Please report this as a issue."
            raise PermissionLevelError(msg)
        if not await has_permission(ctx, level, 9 if or_higher else None):
            logger.error(
                f"{ctx.author} tried to run a command without permission. Command: {ctx.command}, Permission Level: {level} or higher: {or_higher}",
            )
            raise PermissionLevelError(await level_to_name(ctx, level, or_higher))
        logger.info(
            f"{ctx.author} ran command {ctx.command} with permission level {await level_to_name(ctx, level, or_higher)}",
        )
        return True

    return commands.check(predicate)


def ac_has_pl(level: int, or_higher: bool = True):
    async def predicate(ctx: commands.Context[commands.Bot] | discord.Interaction) -> bool:
        if isinstance(ctx, commands.Context):
            logger.error("Context source is not supported for this check, please use has_pl instead.")
            msg = "Context source is not supported for this check, please use has_pl instead. Please report this as a issue."
            raise AppCommandPermissionLevelError(msg)
        if not await has_permission(ctx, level, 9 if or_higher else None):
            logger.error(
                f"{ctx.user} tried to run a command without permission. Command: {ctx.command}, Permission Level: {level} or higher: {or_higher}",
            )
            raise AppCommandPermissionLevelError(await level_to_name(ctx, level, or_higher))
        logger.info(
            f"{ctx.user} ran command {ctx.command} with permission level {await level_to_name(ctx, level, or_higher)}",
        )
        return True

    return app_commands.check(predicate)
