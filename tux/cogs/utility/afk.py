import contextlib
import textwrap
from datetime import UTC, datetime, timedelta
from types import NoneType
from typing import cast
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from prisma.models import AFKModel
from tux.bot import Tux
from tux.database.controllers import AfkController
from tux.utils.constants import CONST
from tux.utils.flags import generate_usage


async def add_afk(
    db: AfkController,
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

    await db.insert_afk(target.id, target.display_name, reason, guild_id, is_perm, until, enforced)

    with contextlib.suppress(discord.Forbidden):
        await target.edit(nick=new_name)


async def del_afk(db: AfkController, target: discord.Member, nickname: str) -> None:
    await db.remove_afk(target.id)
    with contextlib.suppress(discord.Forbidden):
        await target.edit(nick=nickname)


# TODO: add `afk until` command, or add support for providing a timeframe in the regular `afk` and `permafk` commands
class Afk(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = AfkController()
        self.handle_afk_expiration.start()
        self.afk.usage = generate_usage(self.afk)
        self.permafk.usage = generate_usage(self.permafk)

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

        await add_afk(self.db, shortened_reason, target, ctx.guild.id, False)
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
            await del_afk(self.db, target, entry.nickname)
            return await ctx.send("Welcome back!")

        shortened_reason = textwrap.shorten(reason, width=100, placeholder="...")
        await add_afk(self.db, shortened_reason, target, ctx.guild.id, True)

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
            f'{mentioned.mention} is currently AFK {f"until <t:{int(afk.until.timestamp())}:f>" if afk.until is not None else ""}: "{afk.reason}" [<t:{int(afk.since.timestamp())}:R>]'
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

    @tasks.loop(seconds=120)
    async def handle_afk_expiration(self):
        """
        Check AFK database at a regular interval,
        Remove AFK from users with an entry that has expired.
        """
        guilds = self.bot.guilds
        for guild in guilds:
            entries = await self.db.get_all_afk_members(guild.id)
            for entry in entries:
                if entry.until is not None and entry.until < datetime.now(UTC):
                    member = guild.get_member(entry.member_id)
                    if member is None:
                        # Handles the edge case of a user leaving the guild while still temp-AFK
                        await self.db.remove_afk(entry.member_id)
                    else:
                        await del_afk(self.db, member, entry.nickname)


async def setup(bot: Tux):
    await bot.add_cog(Afk(bot))
