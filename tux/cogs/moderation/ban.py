import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.enums import CaseType
from tux.utils.flags import BanFlags

from . import (
    cleanup_failed_case,
    create_mod_log_embed,
    insert_case,
    insert_user_and_moderator,
    send_embed_to_mod_log,
    send_temporary_message,
)

mod_log_channel_id = CONST.LOG_CHANNELS["MOD"]


async def ban_user(ctx: commands.Context[commands.Bot], target: discord.Member, flags: BanFlags) -> None:
    case = None
    try:
        await insert_user_and_moderator(target, ctx)
        case = await insert_case(target, ctx, CaseType.BAN, flags.reason)
    except Exception as db_error:
        await send_temporary_message(ctx, f"Database operation failed. Error: {db_error}")
    dm_sent = await dm_user(
        ctx,
        target,
        f"You have been banned from {ctx.guild} for the following reason: {flags.reason}",
    )

    banned = await perform_ban(ctx, target, flags)

    if banned:
        embed = create_mod_log_embed(
            ctx, f"Case #{case.case_number if case else 'N/A'} - Ban Added", CONST.COLORS["RED"]
        )

        embed.add_field(name="Moderator", value=f"__{ctx.author.name}__\n`{ctx.author.id}`", inline=True)

        embed.add_field(
            name="Target",
            value=f"{'📬' if dm_sent else ''} __{target.name}__\n`{target.id}`",
            inline=True,
        )

        embed.add_field(name="Reason", value=f"> {flags.reason}")

        await send_embed_to_mod_log(ctx, mod_log_channel_id, embed)

        await send_temporary_message(ctx, f"{target.name} has been banned for the following reason: {flags.reason}")

    else:
        await cleanup_failed_case(case)

        await send_temporary_message(ctx, f"Failed to ban {target.name} for the following reason: {flags.reason}")


async def dm_user(ctx: commands.Context[commands.Bot], target: discord.Member, message: str) -> bool:
    try:
        await target.send(message)
        dm_sent = True
    except discord.Forbidden:
        await send_temporary_message(ctx, f"Failed to send a DM to {target.name} regarding the ban.")
        dm_sent = False
    return dm_sent


async def perform_ban(ctx: commands.Context[commands.Bot], target: discord.Member, flags: BanFlags) -> bool:
    try:
        await target.ban(reason=flags.reason, delete_message_days=flags.purge_days)
        banned = True
    except (discord.Forbidden, discord.HTTPException):
        await send_temporary_message(ctx, f"Failed to ban {target.name} for the following reason: {flags.reason}")
        banned = False
    return banned


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command(
        name="ban",
        description="Issues a ban to a member of the server.",
        aliases=["b"],
        usage="$ban @member -r foo -p 7",
    )
    async def ban(self, ctx: commands.Context[commands.Bot], target: discord.Member, *, flags: BanFlags) -> None:
        if not ctx.guild:
            return

        await ban_user(ctx, target, flags)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
