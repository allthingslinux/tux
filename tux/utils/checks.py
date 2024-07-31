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
    """
    Check if a user has a permission level.

    Parameters
    ----------
    source : commands.Context[commands.Bot] | discord.Interaction
        The source object for the command.
    lower_bound : int
        The lower bound of the permission level.
    higher_bound : int | None, optional
        The higher bound of the permission level, by default None.

    Returns
    -------
    bool
        Whether the user has the permission level.
    """

    # If the higher bound is not set, set it to the lower bound
    if higher_bound is None:
        higher_bound = lower_bound

    # If the source is a context object and the guild is None, return False if the lower bound is not 0
    if source.guild is None:
        logger.debug("Guild is None, returning False if lower bound is not 0")
        return lower_bound == 0

    # Determine the source type
    if isinstance(source, commands.Context):
        ctx, interaction = source, None
    else:
        interaction, ctx = source, None

    # Initialize the list of roles to an empty list to avoid type errors
    roles: list[Any] = []

    try:
        # Single level check
        if higher_bound == lower_bound:
            role_id = await get_perm_level_role_id(source, f"perm_level_{lower_bound}_role_id")
            if role_id:
                roles.append(role_id)
            else:
                logger.debug(f"No Role ID fetched for perm_level_{lower_bound}_role_id")

        # Range check
        else:
            fetched_roles = await get_perm_level_roles(source, lower_bound)
            if fetched_roles:
                roles.extend(fetched_roles)
            else:
                logger.debug(f"No roles fetched for levels above and equal to {lower_bound}")

        # Initialize the author/member object to None to avoid type errors
        author: discord.Member | None = None

        # Fetch the author/member object from the context or interaction object
        if ctx and ctx.guild:
            author = await ctx.guild.fetch_member(ctx.author.id)
        elif interaction and interaction.guild:
            author = await interaction.guild.fetch_member(interaction.user.id)

        # Check if the author has any of the roles in the list of roles
        is_authorized = any(role.id in roles for role in author.roles) if author else False
        if is_authorized:
            return True

    except Exception as e:
        logger.error(f"Exception in permission check: {e}")

    # Fallback Path: Sysadmin/Bot Owner Check
    logger.debug("All checks failed, checking for sysadmin or bot owner status")

    try:
        if ctx:
            # Check if the author is a sysadmin or the bot owner for contexts
            if 8 in range(lower_bound, higher_bound + 1) and ctx.author.id in CONST.SYSADMIN_IDS:
                logger.debug("User is a sysadmin")
                return True
            if 9 in range(lower_bound, higher_bound + 1) and ctx.author.id == CONST.BOT_OWNER_ID:
                logger.debug("User is the bot owner")
                return True
        else:
            # Check if the author is a sysadmin or the bot owner for interactions
            if interaction and 8 in range(lower_bound, higher_bound + 1) and interaction.user.id in CONST.SYSADMIN_IDS:
                logger.debug("User is a sysadmin")
                return True
            if interaction and 9 in range(lower_bound, higher_bound + 1) and interaction.user.id == CONST.BOT_OWNER_ID:
                logger.debug("User is the bot owner")
                return True

    except Exception as e:
        logger.error(f"Exception while checking sysadmin or bot owner status: {e}")

    logger.debug("All checks failed, returning False")

    # If all checks fail, return False
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

    # Check if the level is 8 or 9 and return the corresponding name
    if level in {8, 9}:
        return "Sys Admin" if level == 8 else "Bot Owner"

    # Check if the source is a context object and the guild is not None
    if isinstance(source, commands.Context):
        ctx = source
        if ctx.guild is None:
            return "Error"

        # Get the role ID from the database for the guild and the role field
        role_id = await db.get_perm_level_role(ctx.guild.id, f"perm_level_{level}_role_id")
        if role_id and (role := ctx.guild.get_role(role_id)):
            return f"{role.name} or higher" if or_higher else role.name

    else:
        # Get the interaction object and check if it exists and is in a guild
        interaction = source
        if not interaction or not interaction.guild:
            return "Error"

        # Get the role ID from the database for the guild and the role field
        role_id = await db.get_perm_level_role(interaction.guild.id, f"perm_level_{level}_role_id")
        if role_id and (role := interaction.guild.get_role(role_id)):
            return f"{role.name} or higher" if or_higher else role.name

    # Dictionary of permission levels with the level as the key and the name as the value
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

    # Return the name of the permission level from the dictionary
    # or the name of the permission level with "or higher" appended if or_higher is True
    return f"{dictionary[level]} or higher" if or_higher else dictionary[level]


async def get_perm_level_role_id(
    source: commands.Context[commands.Bot] | discord.Interaction,
    level: str,
) -> int | None:
    """
    Get the role ID for a permission level.

    Parameters
    ----------
    source : commands.Context[commands.Bot] | discord.Interaction
        The source object for the command.
    level : str
        The permission level to get the role ID for.

    Returns
    -------
    int | None
        The role ID for the permission level or None if it does not exist.
    """

    # Initialize the role ID to None to avoid type errors
    role_id = None

    try:
        # Check if the source is a context object and if the guild is not None
        if isinstance(source, commands.Context):
            ctx = source
            if ctx.guild is None:
                return None

            # Get the role ID from the database for the guild and the role field
            role_id = await db.get_perm_level_role(ctx.guild.id, level)

        else:
            # Get the interaction object and check if it exists and is in a guild
            interaction = source
            if not interaction or not interaction.guild:
                return None

            # Get the role ID from the database for the guild and the role field
            role_id = await db.get_perm_level_role(interaction.guild.id, level)

    except Exception as e:
        logger.error(f"Error retrieving role ID for level {level}: {e}")

    return role_id


async def get_perm_level_roles(
    source: commands.Context[commands.Bot] | discord.Interaction,
    lower_bound: int,
) -> list[int] | None:
    """
    Get the role IDs for a range of permission levels.

    Parameters
    ----------
    source : commands.Context[commands.Bot] | discord.Interaction
        The source object for the command.
    lower_bound : int
        The lower bound of the permission level.

    Returns
    -------
    list[int] | None
        The list of role IDs for the permission levels or None if they do not exist.
    """

    # Dictionary of permission level roles with the level as the key and the field name as the value
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

    # Initialize the list of role IDs to an empty list to avoid type errors
    role_ids: list[int] = []

    try:
        # For each level in the range of the lower bound to 8
        for level in range(lower_bound, 8):
            # If the role field exists, get the role ID by the field name (e.g. perm_level_1_role_id)
            if role_field := perm_level_roles.get(level):
                # Get the role ID from the database for the guild and the role field
                role_id = await db.get_guild_config_field_value(source.guild.id, role_field)  # type: ignore
                # If the role ID exists, append it to the list of role IDs
                if role_id:
                    role_ids.append(role_id)
                else:
                    logger.debug(f"No role ID found for {role_field}, skipping")

    # Catch any exceptions that occur while getting the role IDs
    except KeyError as e:
        logger.error(f"Key error when accessing role field: {e}")
    except AttributeError as e:
        logger.error(f"Attribute error, likely due to accessing a wrong attribute: {e}")
    except Exception as e:
        logger.error(f"General error getting perm level roles: {e}")
        return None

    return role_ids


def has_pl(level: int, or_higher: bool = True):
    """
    Check if a user has a permission level via a decorator for prefix and hybrid commands.

    Parameters
    ----------
    level : int
        The permission level to check.
    or_higher : bool, optional
        Whether the user should have the permission level or higher, by default True.

    Returns
    -------
    commands.check
        The check for the permission level
    """

    async def predicate(ctx: commands.Context[commands.Bot] | discord.Interaction) -> bool:
        """
        Check if the user has the permission level.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot] | discord.Interaction
            The context or interaction object for the command.

        Returns
        -------
        bool
            Whether the user has the permission level.

        Raises
        ------
        PermissionLevelError
            If the user does not have the permission level.
        """

        if isinstance(ctx, discord.Interaction):
            logger.error("Incorrect checks decorator used. Please use ac_has_pl instead.")
            msg = "Incorrect checks decorator used. Please use ac_has_pl instead and report this as a issue."

            raise PermissionLevelError(msg)

        if not await has_permission(ctx, level, 9 if or_higher else None):
            logger.error(
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
    Check if a user has a permission level via a decorator for app commands.

    Parameters
    ----------
    level : int
        The permission level to check.
    or_higher : bool, optional
        Whether the user should have the permission level or higher, by default True.

    Returns
    -------
    app_commands.check
        The check for the permission level
    """

    async def predicate(ctx: commands.Context[commands.Bot] | discord.Interaction) -> bool:
        """
        Check if the user has the permission level.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot] | discord.Interaction
            The context or interaction object for the command.

        Returns
        -------
        bool
            Whether the user has the permission level.

        Raises
        ------
        AppCommandPermissionLevelError
            If the user does not have the permission level.
        """

        if isinstance(ctx, commands.Context):
            logger.error("Incorrect checks decorator used. Please use has_pl instead.")
            msg = "Incorrect checks decorator used. Please use has_pl instead and report this as a issue."

            raise AppCommandPermissionLevelError(msg)

        if not await has_permission(ctx, level, 9 if or_higher else None):
            logger.error(
                f"{ctx.user} tried to run a command without perms. Command: {ctx.command}, Perm Level: {level} or higher: {or_higher}",
            )

            raise AppCommandPermissionLevelError(await level_to_name(ctx, level, or_higher))

        logger.info(
            f"{ctx.user} ran command {ctx.command} with perm level {await level_to_name(ctx, level, or_higher)}",
        )

        return True

    return app_commands.check(predicate)
