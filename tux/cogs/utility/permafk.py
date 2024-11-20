import contextlib
import textwrap

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers import AfkController
from tux.utils.constants import CONST
from tux.utils.flags import generate_usage


class PERMAFK(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = AfkController()
        self.permafk.usage = generate_usage(self.permafk)

    async def remove_afk(self, target: int) -> None:
        await self.db.remove_afk(target)

    @commands.hybrid_command(name="permafk")
    @commands.guild_only()
    async def permafk(self, ctx: commands.Context[Tux], *, reason: str = "No reason.") -> discord.Message:
        """
        Set yourself permanently AFK so it doesnt remove your afk status if you send a message.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        reason : str, optional
            The reason you are AFK.
        """
        target = ctx.author
        assert ctx.guild
        assert isinstance(target, discord.Member)
        if await self.db.is_afk(target.id, guild_id=ctx.guild.id):
            await self.remove_afk(target.id)
            return await ctx.send("Welcome back!")

        if len(target.display_name) >= CONST.NICKNAME_MAX_LENGTH - 6:
            truncated_name = f"{target.display_name[: CONST.NICKNAME_MAX_LENGTH - 9]}..."
            new_name = f"[AFK] {truncated_name}"
        else:
            new_name = f"[AFK] {target.display_name}"

        shortened_reason = textwrap.shorten(reason, width=100, placeholder="...")
        await self.db.insert_afk(target.id, target.display_name, shortened_reason, ctx.guild.id, True)

        with contextlib.suppress(discord.Forbidden):
            await target.edit(nick=new_name)
        return await ctx.send(
            content="\N{SLEEPING SYMBOL} || You are now permanently afk! To remove afk run this command again."
            + f"Reason: `{shortened_reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )


async def setup(bot: Tux):
    await bot.add_cog(PERMAFK(bot))
