import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.handlers.error import PermissionLevelError

db = DatabaseController().guild_config


async def has_permission(
    source: commands.Context[commands.Bot] | discord.Interaction,
    lower_bound: int,
    higher_bound: int | None = None,
) -> bool:
    """
    Check if the user has permission level between the lower and higher bounds.

    Parameters
    ----------
    source : commands.Context[commands.Bot] | discord.Interaction
        The source of the command.
    lower_bound : int
        The lower bound of the permission level.
    higher_bound : int, optional
        The higher bound of the permission level, by default None
    """

    # if higher_bound is None:
    #     logger.debug(f"Setting higher bound to {lower_bound}")
    #     higher_bound = lower_bound

    # if ctx.guild is None:
    #     logger.debug("Guild is None, returning False if lower bound is not 0 (Everyone)")
    #     return lower_bound == 0

    # # if the source is ctx
    # if isinstance(source, commands.Context):
    #     ctx = source
    #     if ctx.guild is None:
    #         logger.debug("Guild is None, returning False if lower bound is not 0 (Everyone)")
    #         return lower_bound == 0
    # # if the source is an interaction
    # else:
    #     interaction = source
    #     if not interaction:
    #         logger.debug("Channel is None, returning False if lower bound is not 0 (Everyone)")
    #         return lower_bound == 0

    # # get the role ids of the permission levels
    # if higher_bound == lower_bound:
    #     logger.debug(f"Getting role id for permission level {lower_bound}")
    #     roles = [await get_perm_level_role_id(source, f"perm_level_{lower_bound}_role_id")]
    # else:
    #     logger.debug(f"Getting role ids for permission levels above and equal to {lower_bound}")
    #     roles = await get_perm_level_roles(source, lower_bound)

    if isinstance(source, commands.Context):
        ctx = source
        if ctx.guild is None:
            return lower_bound == 0
        if higher_bound is None:
            higher_bound = lower_bound

        roles = (
            await get_perm_level_roles(ctx, lower_bound)
            if higher_bound != lower_bound
            else [await get_perm_level_role_id(ctx, f"perm_level_{lower_bound}_role_id")]
        )

        author = await commands.MemberConverter().convert(ctx, str(ctx.author.id))

        for role in author.roles:
            if role.id in roles:
                return True

    else:
        interaction = source
        if not interaction.guild:
            return lower_bound == 0
        if higher_bound is None:
            higher_bound = lower_bound
        roles = (
            await get_perm_level_roles(interaction, lower_bound)
            if higher_bound != lower_bound
            else [await get_perm_level_role_id(interaction, f"perm_level_{lower_bound}_role_id")]
        )

    # get the role ids of the permission level
    # # get the role ids of the permission levels
    # if higher_bound == lower_bound:
    #     logger.debug(f"Getting role id for permission level {lower_bound}")
    #     roles = [await get_perm_level_role_id(ctx, f"perm_level_{lower_bound}_role_id")]
    # else:
    #     logger.debug(f"Getting role ids for permission levels above and equal to {lower_bound}")
    #     roles = await get_perm_level_roles(ctx, lower_bound)

    # # Convert the context author to a member object because ctx.author defaults to a User object first?
    # author = await commands.MemberConverter().convert(ctx, str(ctx.author.id))
    # for role in author.roles:
    #     if role.id in roles:
    #         logger.debug(f"User has permission level {lower_bound} or higher")
    #         return True

    # # check sysadmins and bot owner
    # # if the bound includes sysadmin or bot owner, check if the user is a sysadmin or bot owner
    # # (sysadmin is 8, bot owner is 9)
    # logger.debug("Checking if user is a sysadmin or bot owner")
    # if 8 in range(lower_bound, higher_bound + 1) and ctx.author.id in CONST.SYSADMIN_IDS:
    #     logger.debug("User is a sysadmin")
    #     return True

    # if 9 in range(lower_bound, higher_bound + 1) and ctx.author.id == CONST.BOT_OWNER_ID:
    #     logger.debug("User is the bot owner")
    #     return True

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

    # These ideally should map to the role names, not these example names?

    # role ids, we should also make the controller be able to return the user ids so its easier
    # settings.json is all setup for that, see constants.py for how its done
    # dictionary = {
    #     0: "Member",
    #     1: "Support",
    #     2: "Junior Moderator",
    #     3: "Moderator",
    #     4: "Senior Moderator",
    #     5: "Administrator",
    #     6: "Head Administrator",
    #     7: "Server Owner",
    #     8: "Sys Admin",
    #     9: "Bot Owner",
    # }

    # if or_higher:
    #     return f"{dictionary[level]} or higher"
    # return dictionary[level]

    # get the role name from the role id

    # if the source is ctx
    if isinstance(source, commands.Context):
        ctx = source
        if ctx.guild is None:
            return "Error"
        role_id = await db.get_perm_level_role(ctx.guild.id, f"perm_level_{level}_role_id")
        if role_id:
            role = ctx.guild.get_role(role_id)
            if role:
                return role.name if not or_higher else f"{role.name} or higher"

    # if the source is an interaction
    else:
        interaction = source
        if not interaction:
            return "Error"
        if not interaction.guild:
            return "Error"
        role_id = await db.get_perm_level_role(interaction.guild.id, f"perm_level_{level}_role_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                return role.name if not or_higher else f"{role.name} or higher"

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

    return dictionary[level] if not or_higher else f"{dictionary[level]} or higher"


async def get_perm_level_role_id(
    source: commands.Context[commands.Bot] | discord.Interaction,
    level: str,
) -> int | None:
    """
    Get the role id of the permission level.

    Parameters
    ----------
    ctx : commands.Context[commands.Bot]
        The discord context object.
    level : str
        The permission level to get the role id of.
        e.g. ("perm_level_0_role_id", "perm_level_1_role_id", etc.)

    Returns
    -------
    int | None
        The role id of the permission level
    """

    # if the source is ctx
    if isinstance(source, commands.Context):
        ctx = source
        if ctx.guild is None:
            return None
        return await db.get_perm_level_role(ctx.guild.id, level) or None
    interaction = source
    if not interaction:
        return None
    if not interaction.guild:
        return None
    return await db.get_perm_level_role(interaction.guild.id, level) or None


async def get_perm_level_roles(
    source: commands.Context[commands.Bot] | discord.Interaction,
    lower_bound: int,
) -> list[int] | None:
    """
    Get the role ids of the permission levels between the lower and higher bounds.

    Parameters
    ----------
    ctx : commands.Context[commands.Bot]
        The discord context object.
    lower_bound : int
        The lower bound of the permission level.

    Returns
    -------
    list[int]
        The role ids of the permission levels
    """

    # if the source is ctx
    if isinstance(source, commands.Context):
        ctx = source
        if ctx.guild is None:
            return None
        return await db.get_perm_level_roles(ctx.guild.id, lower_bound) or []
    interaction = source
    if not interaction:
        return None
    if not interaction.guild:
        return None
    return await db.get_perm_level_roles(interaction.guild.id, lower_bound) or []


# checks if the user has permission level 1 (Support)
def has_pl(level: int, or_higher: bool = True):
    """
    Check if the user has a permission level equal to or higher than the given level.

    Parameters
    ----------
    level : int
        The permission level to check against.
    or_higher : bool, optional
        Whether the user should have the permission level or higher, by default False
    """

    async def predicate(source: commands.Context[commands.Bot] | discord.Interaction) -> bool:
        # if not await has_permission(ctx, level, 9 if or_higher else None):
        #     logger.error(f"{ctx.author} tried to run a command without permission. Command: {ctx.command}, Permission Level: {level} or higher: {or_higher}")
        #     raise PermissionLevelError(await level_to_name(ctx, level, or_higher))
        # logger.info(f"{ctx.author} ran command {ctx.command} with permission level {await level_to_name(ctx, level, or_higher)}")
        # return True

        # if source is ctx
        if isinstance(source, commands.Context):
            logger.debug("Checking permission level for context")
            ctx = source
            if ctx.guild is None:
                return False
            if not await has_permission(ctx, level, 9 if or_higher else None):
                logger.error(
                    f"{ctx.author} tried to run a command without permission. Command: {ctx.command}, Permission Level: {level} or higher: {or_higher}",
                )
                raise PermissionLevelError(await level_to_name(ctx, level, or_higher))
            logger.info(
                f"{ctx.author} ran command {ctx.command} with permission level {await level_to_name(ctx, level, or_higher)}",
            )
            return True
        logger.debug("Checking permission level for interaction")
        interaction = source
        if not interaction:
            return False
        if not interaction.guild:
            return False
        if not await has_permission(interaction, level, 9 if or_higher else None):
            logger.error(
                f"{interaction.user} tried to run a command without permission. Command: {interaction.command}, Permission Level: {level} or higher: {or_higher}",
            )
            raise PermissionLevelError(await level_to_name(interaction, level, or_higher))
        logger.info(
            f"{interaction.user} ran command {interaction.command} with permission level {await level_to_name(interaction, level, or_higher)}",
        )
        return True

    return commands.check(predicate)
