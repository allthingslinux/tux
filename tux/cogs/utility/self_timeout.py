from datetime import UTC, datetime, timedelta
from types import NoneType

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.cogs.utility import add_afk, del_afk
from tux.database.controllers import DatabaseController
from tux.ui.views.confirmation import ConfirmationDanger
from tux.utils.flags import generate_usage
from tux.utils.functions import convert_to_seconds, seconds_to_human_readable


class SelfTimeout(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.self_timeout.usage = generate_usage(self.self_timeout)

    async def request_confirmation(
        self,
        member: discord.Member,
        guild_name: str,
        duration: str,
        reason: str,
    ) -> bool | NoneType:
        """
        Send a self-timeout confirmation dialog to a member

        Parameters
        ----------
        member:
            The discord user or member object representing the account to message

        guild_name (str):
            The name of the guild the confirmation is being sent from

        duration (str) :
            human readable string describing the duration of the self-timeout

        reason (str):
            Why the user has stated they are timing themself out

        Returns
        -------
        Bool | NoneType
            True if the user has confirmed
            False if the user cancelled
            None if the confirmation message failed to send
        """

        view = ConfirmationDanger()

        try:
            message_content = f'### WARNING\n### You are about to be timed out in the guild "{guild_name}" for {duration} with the reason "{reason}".\nas soon as you confirm this, **you cannot cancel it or remove it early**. There is *no* provision for it to be removed by server staff on request. please think very carefully and make sure you\'ve entered the correct values before you proceed with this command.'

            confirmation_message = await member.send(
                content=message_content,
                view=view,
            )

        except discord.Forbidden:
            return None

        await view.wait()
        await confirmation_message.delete()

        return view.value

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

        if duration_seconds < 300:
            await ctx.send("Error! duration cannot be less than 5 minutes!")
            return

        entry = await self.db.afk.get_afk_member(member.id, guild_id=ctx.guild.id)

        if entry is not None and reason == "No Reason.":
            # If the member is already afk and hasn't provided a reason with this command,
            # assume they want to upgrade their current AFK to a self-timeout and carry the old reason
            reason = entry.reason

        confirmed = await self.request_confirmation(member, ctx.guild.name, duration_readable, reason)

        if confirmed is None:
            await ctx.send("Confirmation failed to send or timed out.")
            return

        if confirmed:
            await member.send(
                f'You have timed yourself out in guild {ctx.guild.name} for {duration_readable} with the reason "{reason}".',
            )

            if entry is not None:
                await del_afk(self.db, member, entry.nickname)

            await member.timeout(timedelta(seconds=float(duration_seconds)), reason="self time-out")

            await add_afk(
                self.db,
                reason,
                member,
                ctx.guild.id,
                True,
                datetime.now(UTC) + timedelta(seconds=duration_seconds),
                True,
            )


async def setup(bot: Tux):
    await bot.add_cog(SelfTimeout(bot))
