import re
from datetime import UTC, datetime, timedelta

import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.utils import checks
from tux.utils.flags import TimeoutFlags

from . import ModerationCogBase


def parse_time_string(time_str: str) -> timedelta:
    """
    Convert a string representation of time (e.g., '60s', '1m', '2h', '10d')
    into a datetime.timedelta object.

    Parameters
    time_str (str): The string representation of time.

    Returns
    timedelta: Corresponding timedelta object.
    """

    # Define regex pattern to parse time strings
    time_pattern = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])$")

    # Match the input string with the pattern
    match = time_pattern.match(time_str)

    if not match:
        msg = f"Invalid time format: '{time_str}'"
        raise ValueError(msg)

    # Extract the value and unit from the pattern match
    value = int(match["value"])
    unit = match["unit"]

    # Define the mapping of units to keyword arguments for timedelta
    unit_map = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}

    # Check if the unit is in the map
    if unit not in unit_map:
        msg = f"Unknown time unit: '{unit}'"
        raise ValueError(msg)

    # Create the timedelta with the appropriate keyword argument
    kwargs = {unit_map[unit]: value}

    return timedelta(**kwargs)


class Timeout(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="timeout",
        aliases=["t", "to", "mute"],
        usage="timeout [target] [duration] [reason]",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def timeout(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: TimeoutFlags,
    ) -> None:
        """
        Timeout a member from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The member to timeout.
        flags : TimeoutFlags
            The flags for the command.

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """

        if ctx.guild is None:
            logger.warning("Timeout command used outside of a guild context.")
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, target, moderator, "timeout"):
            return

        if target.is_timed_out():
            await ctx.send(f"{target} is already timed out.", delete_after=30, ephemeral=True)
            return

        duration = parse_time_string(flags.duration)

        try:
            await target.timeout(duration, reason=flags.reason)

        except discord.DiscordException as e:
            await ctx.send(f"Failed to timeout {target}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.TIMEOUT,
            case_reason=flags.reason,
            case_expires_at=datetime.now(UTC) + duration,
            guild_id=ctx.guild.id,
        )

        await self.send_dm(ctx, flags.silent, target, flags.reason, f"timed out for {flags.duration}")
        await self.handle_case_response(ctx, CaseType.TIMEOUT, case.case_id, flags.reason, target, flags.duration)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Timeout(bot))
