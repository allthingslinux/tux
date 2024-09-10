from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.utils.constants import CONST
from tux.utils.exceptions import AppCommandPermissionLevelError, PermissionLevelError

db = DatabaseController().guild_config

T = TypeVar("T", bound=commands.Context[Tux] | discord.Interaction)


async def fetch_guild_config(guild_id: int) -> dict[str, Any]:
    """Fetch all relevant guild config data in a single DB call."""
    config = await db.get_guild_config(guild_id)
    return {f"perm_level_{i}_role_id": getattr(config, f"perm_level_{i}_role_id", None) for i in range(8)}


async def has_permission(
    source: commands.Context[Tux] | discord.Interaction,
    lower_bound: int,
    higher_bound: int | None = None,
) -> bool:
    """Check if the source has the required permission level."""
    higher_bound = higher_bound or lower_bound

    if source.guild is None:
        return lower_bound == 0

    author = source.author if isinstance(source, commands.Context) else source.user
    guild_config = await fetch_guild_config(source.guild.id)

    roles = [guild_config[f"perm_level_{i}_role_id"] for i in range(lower_bound, min(higher_bound + 1, 8))]
    roles = [role for role in roles if role is not None]

    if isinstance(author, discord.Member) and any(role in [r.id for r in author.roles] for role in roles):
        return True

    return (8 in range(lower_bound, higher_bound + 1) and author.id in CONST.SYSADMIN_IDS) or (
        9 in range(lower_bound, higher_bound + 1) and author.id == CONST.BOT_OWNER_ID
    )


async def level_to_name(
    source: commands.Context[Tux] | discord.Interaction,
    level: int,
    or_higher: bool = False,
) -> str:
    """Get the name of the permission level."""
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
    """Generic permission check for both prefix and slash commands."""

    async def predicate(ctx: commands.Context[Tux] | discord.Interaction) -> bool:
        if not await has_permission(ctx, level, 9 if or_higher else None):
            name = await level_to_name(ctx, level, or_higher)
            logger.info(
                f"{ctx.author if isinstance(ctx, commands.Context) else ctx.user} tried to run a command without perms. Command: {ctx.command}, Perm Level: {level} or higher: {or_higher}",
            )
            raise (PermissionLevelError if isinstance(ctx, commands.Context) else AppCommandPermissionLevelError)(name)

        logger.info(
            f"{ctx.author if isinstance(ctx, commands.Context) else ctx.user} ran command {ctx.command} with perm level {await level_to_name(ctx, level, or_higher)}",
        )
        return True

    return predicate


def has_pl(level: int, or_higher: bool = True):
    """Check for traditional "prefix" commands."""

    async def wrapper(ctx: commands.Context[Tux]) -> bool:
        if isinstance(ctx, discord.Interaction):
            msg = "Incorrect checks decorator used. Please use ac_has_pl instead and report this as an issue."
            raise PermissionLevelError(msg)
        return await permission_check(level, or_higher)(ctx)

    return commands.check(wrapper)


def ac_has_pl(level: int, or_higher: bool = True):
    """Check for application "slash" commands."""

    async def wrapper(interaction: discord.Interaction) -> bool:
        if isinstance(interaction, commands.Context):
            msg = "Incorrect checks decorator used. Please use has_pl instead and report this as an issue."
            raise AppCommandPermissionLevelError(msg)
        return await permission_check(level, or_higher)(interaction)

    return app_commands.check(wrapper)
