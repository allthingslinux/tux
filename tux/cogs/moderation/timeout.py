import datetime

import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import TimeoutFlags
from tux.utils.functions import parse_time_string
from tux.utils.mixed_args import generate_mixed_usage, is_duration

from . import ModerationCogBase


class Timeout(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Generate flexible usage that shows both formats
        self.timeout.usage = generate_mixed_usage("timeout", ["member"], ["duration", "reason"], ["-d duration", "-s"])

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
        duration_or_reason: str | None = None,
        *,
        flags: TimeoutFlags | None = None,
    ) -> None:
        """
        Timeout a member from the server.

        Supports both positional and flag-based arguments:
        - Positional: `timeout @user 14d reason`
        - Flag-based: `timeout @user reason -d 14d`
        - Mixed: `timeout @user 14d reason -s`

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to timeout.
        duration_or_reason : Optional[str]
            Either a duration (e.g., "14d") or reason if using positional format.
        flags : Optional[TimeoutFlags]
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

        # Parse arguments - support both positional and flag formats
        duration = None
        reason = None
        silent = False

        # Check if duration_or_reason is a duration (time pattern)
        if duration_or_reason and is_duration(duration_or_reason):
            duration = duration_or_reason
            # If flags are provided, use them for reason and silent
            if flags:
                reason = flags.reason
                silent = flags.silent
            else:
                # No flags provided, assume remaining arguments are reason
                reason = "No reason provided"
        else:
            # duration_or_reason is not a duration, treat as reason
            if duration_or_reason:
                reason = duration_or_reason
            elif flags:
                reason = flags.reason
            else:
                reason = "No reason provided"

            # Use flags for duration and silent if provided
            if flags:
                duration = flags.duration
                silent = flags.silent

        # Validate that we have a duration
        if not duration:
            await ctx.send("Duration is required. Use format like '14d', '1h', etc.", ephemeral=True)
            return

        # Parse and validate duration
        try:
            parsed_duration = parse_time_string(duration)

            # Discord maximum timeout duration is 28 days
            max_duration = datetime.timedelta(days=28)
            if parsed_duration > max_duration:
                await ctx.send(
                    "Timeout duration exceeds Discord's maximum of 28 days. Setting timeout to maximum allowed (28 days).",
                    ephemeral=True,
                )
                parsed_duration = max_duration
                # Update the display duration for consistency
                duration = "28d"
        except ValueError as e:
            await ctx.send(f"Invalid duration format: {e}", ephemeral=True)
            return

        # Execute timeout with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.TIMEOUT,
            user=member,
            reason=reason,
            silent=silent,
            dm_action=f"timed out for {duration}",
            actions=[(member.timeout(parsed_duration, reason=reason), type(None))],
            duration=duration,
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Timeout(bot))
