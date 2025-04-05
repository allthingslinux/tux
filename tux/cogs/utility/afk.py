import contextlib
import textwrap
from datetime import datetime, timedelta
from typing import cast
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from prisma.models import AFKModel
from tux.bot import Tux
from tux.database.controllers import AfkController
from tux.utils.constants import CONST
from tux.utils.flags import generate_usage


class Afk(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = AfkController()
        self.afk.usage = generate_usage(self.afk)
        self.permafk.usage = generate_usage(self.permafk)

    async def add_afk(self, reason: str, target: discord.Member, guild_id: int, is_perm: bool):
        if len(target.display_name) >= CONST.NICKNAME_MAX_LENGTH - 6:
            truncated_name = f"{target.display_name[: CONST.NICKNAME_MAX_LENGTH - 9]}..."
            new_name = f"[AFK] {truncated_name}"
        else:
            new_name = f"[AFK] {target.display_name}"

        await self.db.insert_afk(target.id, target.display_name, reason, guild_id, is_perm)

        with contextlib.suppress(discord.Forbidden):
            await target.edit(nick=new_name)

    async def del_afk(self, target: discord.Member, nickname: str) -> None:
        await self.db.remove_afk(target.id)
        with contextlib.suppress(discord.Forbidden):
            await target.edit(nick=nickname)

    @commands.hybrid_command(
        name="afk",
    )
    @commands.guild_only()
    async def afk(
        self,
        ctx: commands.Context[Tux],
        *,
        reason: str = "No reason.",
    ) -> discord.Message:
        """
        Set yourself as AFK.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        reason : str, optional
            The reason you are AFK.
        """

        target = ctx.author
        shortened_reason = textwrap.shorten(reason, width=100, placeholder="...")

        assert ctx.guild
        assert isinstance(target, discord.Member)

        entry = await self.db.get_afk_member(target.id, guild_id=ctx.guild.id)
        if entry is not None:
            await self.db.remove_afk(target.id)
            await self.db.insert_afk(target.id, entry.nickname, shortened_reason, ctx.guild.id)
            return await ctx.send(
                f"You are already afk, updating AFK reason to `{shortened_reason}`",
                ephemeral=True,
            )

        await self.add_afk(shortened_reason, target, ctx.guild.id, False)
        return await ctx.send(
            content="\N{SLEEPING SYMBOL} || You are now afk! " + f"Reason: `{shortened_reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )

    @commands.hybrid_command(name="permafk")
    @commands.guild_only()
    async def permafk(self, ctx: commands.Context[Tux], *, reason: str = "No reason.") -> discord.Message:
        """
        Set yourself permanently AFK until you rerun the command.

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

        entry = await self.db.get_afk_member(target.id, guild_id=ctx.guild.id)
        if entry is not None:
            await self.del_afk(target, entry.nickname)
            return await ctx.send("Welcome back!")

        shortened_reason = textwrap.shorten(reason, width=100, placeholder="...")
        await self.add_afk(shortened_reason, target, ctx.guild.id, True)

        return await ctx.send(
            content="\N{SLEEPING SYMBOL} || You are now permanently afk! To remove afk run this command again. "
            + f"Reason: `{shortened_reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )

    @commands.Cog.listener("on_message")
    async def remove_afk(self, message: discord.Message) -> None:
        """
        Remove the AFK status of a member when they send a message.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """

        if not message.guild or message.author.bot:
            return

        entry = await self.db.get_afk_member(message.author.id, guild_id=message.guild.id)
        if not entry:
            return

        if entry.since + timedelta(seconds=10) > datetime.now(ZoneInfo("UTC")):
            return
        if await self.db.is_perm_afk(message.author.id, guild_id=message.guild.id):
            return
        assert isinstance(message.author, discord.Member)

        await self.db.remove_afk(message.author.id)

        await message.reply("Welcome back!", delete_after=5)

        with contextlib.suppress(discord.Forbidden):
            await message.author.edit(nick=entry.nickname)

    @commands.Cog.listener("on_message")
    async def check_afk(self, message: discord.Message) -> None:
        """
        Check if a message mentions an AFK member.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """

        if not message.guild:
            return

        if message.author.bot:
            return

        afks_mentioned: list[tuple[discord.Member, AFKModel]] = []

        for mentioned in message.mentions:
            entry = await self.db.get_afk_member(mentioned.id, guild_id=message.guild.id)
            if entry:
                afks_mentioned.append((cast(discord.Member, mentioned), entry))

        if not afks_mentioned:
            return

        msgs: list[str] = [
            f"{mentioned.mention} is currently AFK: `{afk.reason}` (<t:{int(afk.since.timestamp())}:R>)"
            for mentioned, afk in afks_mentioned
        ]

        await message.reply(
            content="\n".join(msgs),
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )


async def setup(bot: Tux):
    await bot.add_cog(Afk(bot))
