import datetime

import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import require_junior_mod
from tux.core.flags import TimeoutFlags
from tux.database.models import CaseType as DBCaseType
from tux.shared.constants import CONST
from tux.shared.functions import parse_time_string

from . import ModerationCogBase


class Timeout(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="timeout",
        aliases=["to", "mute"],
    )
    @commands.guild_only()
    @require_junior_mod()
    async def timeout(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: TimeoutFlags,
    ) -> None:
        """
        Timeout a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to timeout.
        flags : TimeoutFlags
            The flags for the command (duration: str, silent: bool).

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """
        assert ctx.guild

        # Check if target is a bot
        if member.bot:
            await ctx.send(
                "Bots cannot be timed out.",
                ephemeral=True,
                delete_after=CONST.DEFAULT_DELETE_AFTER,
            )
            return

        # Check if member is already timed out
        if member.is_timed_out():
            await ctx.send(
                f"{member} is already timed out.",
                ephemeral=True,
                delete_after=CONST.DEFAULT_DELETE_AFTER,
            )
            return

        # Parse and validate duration
        try:
            duration = parse_time_string(flags.duration)

            # Discord maximum timeout duration is 28 days
            max_duration = datetime.timedelta(days=28)

            if duration > max_duration:
                await ctx.send(
                    "Timeout duration exceeds Discord's maximum of 28 days. Setting timeout to maximum allowed (28 days).",
                    ephemeral=True,
                    delete_after=CONST.DEFAULT_DELETE_AFTER,
                )

                duration = max_duration
                # Update the display duration for consistency
                flags.duration = "28d"

        except ValueError as e:
            await ctx.send(
                f"Invalid duration format: {e}",
                ephemeral=True,
                delete_after=CONST.DEFAULT_DELETE_AFTER,
            )
            return

        # Execute timeout with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.TIMEOUT,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action=f"timed out for {flags.duration}",
            actions=[(lambda: member.timeout(duration, reason=flags.reason), type(None))],
            duration=int(duration.total_seconds()),
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Timeout(bot))
