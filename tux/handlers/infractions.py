from datetime import datetime

import discord
from discord.ext import commands

from tux.cogs.helpers import get_or_insert_moderator, get_or_insert_user
from tux.database.controllers import DatabaseController
from tux.utils.enums import CaseType


async def handle_infraction(
    db_controller: DatabaseController,
    ctx: commands.Context[commands.Bot],
    member: discord.Member,
    reason: str,
    case_type: CaseType,
    expires_at: datetime | None = None,
    purge_days: int | None = None,
) -> None:
    infraction = None

    try:
        moderator = await get_or_insert_moderator(db_controller, ctx)
        user = await get_or_insert_user(db_controller, member)
    except Exception as error:
        await handle_error(ctx, error)
        return

    if user and moderator:
        try:
            infraction = await db_controller.infractions.insert_infraction(
                user.id, moderator.id, infraction_type, reason, expires_at
            )
        except Exception as error:
            await handle_error(ctx, error)
            return

    try:
        await infraction_type_actions[infraction_type](member, reason, purge_days)

    except Exception as error:
        if user and moderator and infraction:
            await db_controller.infractions.delete_infraction(infraction.id)

        await handle_error(ctx, error)
        return

    await ctx.send(f"Successfully {infraction_type.name.lower()}ed {member.mention}.")
    await log_to_discord(ctx, infraction)


async def ban_member(member: discord.Member, reason: str, purge_days: int | None) -> None:
    await member.ban(reason=reason, delete_message_days=purge_days or 0)


async def temp_ban_member(member: discord.Member, reason: str, purge_days: int | None) -> None:
    await member.ban(reason=reason, delete_message_days=purge_days or 0)


async def log_to_discord(ctx: commands.Context[commands.Bot], infraction: Infractions | None) -> None:
    if not infraction:
        return
    await ctx.send(f"Infraction logged: {infraction.id}")


async def handle_error(ctx: commands.Context[commands.Bot], error: Exception) -> None:
    await ctx.send(f"An error occurred: {error}")
    raise error


# other actions like mute, kick, etc can be added here
infraction_type_actions = {
    InfractionType.BAN: ban_member,
    # ...
}
