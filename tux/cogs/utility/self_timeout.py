import contextlib
from datetime import UTC, datetime, timedelta
from types import NoneType

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers import AfkController
from tux.ui.views.confirmation import ConfirmationDanger
from tux.utils.constants import CONST
from tux.utils.flags import generate_usage
from tux.utils.functions import convert_to_seconds, seconds_to_human_readable


class SelfTimeout(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = AfkController()
        self.self_timeout.usage = generate_usage(self.self_timeout)

    async def add_afk(
        self,
        reason: str,
        target: discord.Member,
        guild_id: int,
        is_perm: bool,
        until: datetime | NoneType | None = None,
        enforced: bool = False,
    ):
        if len(target.display_name) >= CONST.NICKNAME_MAX_LENGTH - 6:
            truncated_name = f"{target.display_name[: CONST.NICKNAME_MAX_LENGTH - 9]}..."
            new_name = f"[AFK] {truncated_name}"
        else:
            new_name = f"[AFK] {target.display_name}"

        await self.db.insert_afk(target.id, target.display_name, reason, guild_id, is_perm, until, enforced)

        with contextlib.suppress(discord.Forbidden):
            await target.edit(nick=new_name)

    async def del_afk(self, target: discord.Member, nickname: str) -> None:
        await self.db.remove_afk(target.id)
        with contextlib.suppress(discord.Forbidden):
            await target.edit(nick=nickname)

    @commands.hybrid_command(
        name="self_timeout",
        aliases=["sto", "stimeout", "selftimeout"],
    )
    @commands.guild_only()
    async def self_timeout(self, ctx: commands.Context[Tux], duration: str, *, reason: str = "No Reason.") -> None:
        """
        Time yourself out for a set duration

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command
        duration : str
            How long the timeout should last for
        reason : str [optional]
            The reason why you are timing yourself out
        """
        if ctx.guild is None:
            await ctx.send("Command must be run in a guild!")
            return

        member = ctx.guild.get_member(ctx.author.id)
        if member is None:
            return
        duration_seconds: int = convert_to_seconds(duration)
        duration_readable = seconds_to_human_readable(duration_seconds)

        if duration_seconds > 604800:
            await ctx.send("Error! duration cannot be longer than 7 days!")
            return

        entry = await self.db.get_afk_member(member.id, guild_id=ctx.guild.id)
        if entry is not None and reason == "No Reason.":
            # If the member is already afk and hasn't provided a reason with this command,
            # assume they want to upgrade their current AFK to a self-timeout and carry the old reason
            reason = entry.reason

        view = ConfirmationDanger()
        try:
            confirmation_message = await member.send(
                f'## WARNING\n### You are about to be timed out in the guild "{ctx.guild.name}" for {duration_readable} with the reason "{reason}".\nas soon as you confirm this, **you cannot cancel it or remove it early**. There is *no* provision for it to be removed by server staff on request. please think very carefully and make sure you\'ve entered the correct values before you proceed with this command.',
                view=view,
            )
        except discord.Forbidden:
            await ctx.send("Error: Tux was unable to DM you the confirmation message")
            return

        await view.wait()
        await confirmation_message.delete()
        if view.value:
            await member.send(
                f'You have timed yourself out in guild {ctx.guild.name} for {duration_readable} with the reason "{reason}".',
            )
            if entry is not None:
                await self.del_afk(member, entry.nickname)
            await member.timeout(timedelta(seconds=float(duration_seconds)), reason="self time-out")
            await self.add_afk(
                reason,
                member,
                ctx.guild.id,
                True,
                datetime.now(UTC) + timedelta(seconds=duration_seconds),
                True,
            )


async def setup(bot: Tux):
    await bot.add_cog(SelfTimeout(bot))
