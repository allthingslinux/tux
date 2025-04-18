import contextlib
import textwrap
from datetime import UTC, datetime, timedelta
from typing import cast
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from prisma.models import AFKModel
from tux.bot import Tux
from tux.cogs.utility import add_afk, del_afk
from tux.database.controllers import DatabaseController
from tux.utils.flags import generate_usage
from tux.utils.functions import convert_to_seconds, seconds_to_human_readable

# TODO: add `afk until` command, or add support for providing a timeframe in the regular `afk` and `permafk` commands


class Afk(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
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
    ) -> None:
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

        await add_afk(self.db, shortened_reason, target, ctx.guild.id, False)

        await ctx.reply(
            content="\N{SLEEPING SYMBOL} || You are now afk! " + f"Reason: `{shortened_reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )

    @commands.hybrid_command(name="permafk")
    @commands.guild_only()
    async def permafk(self, ctx: commands.Context[Tux], *, reason: str = "No reason.") -> None:
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

        entry = await self.db.afk.get_afk_member(target.id, guild_id=ctx.guild.id)
        if entry is not None:
            await del_afk(self.db, target, entry.nickname)
            await ctx.reply("Welcome back!")
            return

        shortened_reason = textwrap.shorten(reason, width=100, placeholder="...")

        if entry is not None and reason == "No reason.":
            # If the member is already afk and hasn't provided a reason with this command,
            # assume they want to change the current AFK to a permafk and carry the old reason
            shortened_reason = entry.reason

        await add_afk(self.db, shortened_reason, target, ctx.guild.id, True)

        await ctx.reply(
            content="\N{SLEEPING SYMBOL} || You are now permanently afk! To remove afk run this command again. "
            + f"Reason: `{shortened_reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )

    @commands.hybrid_command(
        name="afk_until",
        aliases=["afku", "uafk", "afkuntil"],
    )
    @commands.guild_only()
    async def afk_until(self, ctx: commands.Context[Tux], duration: str, *, reason: str = "No Reason.") -> None:
        """
        AFK for a set duration

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command
        duration : str
            How long the AFK should last for
        reason : str [optional]
            The reason why you are AFK
        """
        if ctx.guild is None:
            await ctx.reply("Command must be run in a guild!", ephemeral=True)
            return

        member = ctx.guild.get_member(ctx.author.id)
        if member is None:
            return

        duration_seconds: int = convert_to_seconds(duration)
        duration_readable = seconds_to_human_readable(duration_seconds)

        if duration_seconds == 0:
            await ctx.reply("Error! Invalid time format", ephemeral=True)
            return

        if duration_seconds > 604800:
            await ctx.reply("Error! duration cannot be longer than 7 days!", ephemeral=True)
            return

        if duration_seconds < 300:
            await ctx.reply("Error! duration cannot be less than 5 minutes!", ephemeral=True)
            return

        entry = await self.db.afk.get_afk_member(member.id, guild_id=ctx.guild.id)

        if entry is not None and reason == "No Reason.":
            # If the member is already afk and hasn't provided a reason with this command,
            # assume they want to add an expiration to their current AFK and carry the old reason
            reason = entry.reason

        await ctx.reply(
            content="\N{SLEEPING SYMBOL} || You are now afk for" + f" {duration_readable}! Reason: `{reason}`",
            allowed_mentions=discord.AllowedMentions(
                users=False,
                everyone=False,
                roles=False,
            ),
        )
        await add_afk(
            self.db,
            reason,
            member,
            ctx.guild.id,
            True,
            datetime.now(UTC) + timedelta(seconds=duration_seconds),
            False,
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

        assert isinstance(message.author, discord.Member)

        entry = await self.db.afk.get_afk_member(message.author.id, guild_id=message.guild.id)

        if not entry:
            return

        if entry.since + timedelta(seconds=10) > datetime.now(ZoneInfo("UTC")):
            return

        if await self.db.afk.is_perm_afk(message.author.id, guild_id=message.guild.id):
            return

        await self.db.afk.remove_afk(message.author.id)

        await message.reply("Welcome back!", delete_after=5)

        # Suppress Forbidden errors if the bot doesn't have permission to change the nickname
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

        # Check if the message is a self-timeout command.
        # if it is, the member is probably trying to upgrade to a self-timeout, so AFK status should not be removed.
        if message.content.startswith("$sto"):
            return

        afks_mentioned: list[tuple[discord.Member, AFKModel]] = []

        for mentioned in message.mentions:
            entry = await self.db.afk.get_afk_member(mentioned.id, guild_id=message.guild.id)
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
        for guild in self.bot.guilds:
            expired_entries = await self._get_expired_afk_entries(guild.id)

            for entry in expired_entries:
                member = guild.get_member(entry.member_id)

                if member is None:
                    # Handles the edge case of a user leaving the guild while still temp-AFK
                    await self.db.afk.remove_afk(entry.member_id)
                else:
                    await del_afk(self.db, member, entry.nickname)

    async def _get_expired_afk_entries(self, guild_id: int) -> list[AFKModel]:
        """
        Get all expired AFK entries for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check.

        Returns
        -------
        list[AFKModel]
            A list of expired AFK entries.
        """
        entries = await self.db.afk.get_all_afk_members(guild_id)
        current_time = datetime.now(UTC)

        return [entry for entry in entries if entry.until is not None and entry.until < current_time]


async def setup(bot: Tux) -> None:
    await bot.add_cog(Afk(bot))
