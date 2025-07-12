import datetime

import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import TimeoutFlags
from utils.functions import generate_usage, parse_time_string

from prisma.enums import CaseType

from . import ModerationCogBase


class Timeout(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.timeout.usage = generate_usage(self.timeout, TimeoutFlags)

    @commands.hybrid_command(
        name="timeout",
        aliases=["t", "to", "mute", "m"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
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

        # Check if member is already timed out
        if member.is_timed_out():
            await ctx.send(f"{member} is already timed out.", ephemeral=True)
            return

        # Check if moderator has permission to timeout the member
        if not await self.check_conditions(ctx, member, ctx.author, "timeout"):
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
                )
                duration = max_duration
                # Update the display duration for consistency
                flags.duration = "28d"
        except ValueError as e:
            await ctx.send(f"Invalid duration format: {e}", ephemeral=True)
            return

        # Execute timeout with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.TIMEOUT,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action=f"timed out for {flags.duration}",
            actions=[(member.timeout(duration, reason=flags.reason), type(None))],
            duration=flags.duration,
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Timeout(bot))
