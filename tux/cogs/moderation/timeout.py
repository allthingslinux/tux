import re
from datetime import UTC, datetime, timedelta

import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils.constants import Constants as CONST
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
        aliases=["t", "to"],
        usage="$timeout [target] [duration] [reason]",
    )
    @commands.guild_only()
    async def timeout(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: TimeoutFlags,
    ) -> None:
        """
        Timeout a user from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The user to timeout.
        flags : TimeoutFlags
            The flags for the command.

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """

        moderator = await commands.MemberConverter().convert(ctx, str(ctx.author.id))

        if ctx.guild is None:
            logger.warning("Timeout command used outside of a guild context.")
            return
        if target == ctx.author:
            await ctx.reply("You cannot timeout yourself.", delete_after=10, ephemeral=True)
            return
        if target.top_role >= moderator.top_role:
            await ctx.reply("You cannot timeout a user with a higher or equal role.", delete_after=10, ephemeral=True)
            return
        if target == ctx.guild.owner:
            await ctx.reply("You cannot timeout the server owner.", delete_after=10, ephemeral=True)
            return

        duration = parse_time_string(flags.duration)

        try:
            await self.send_dm(ctx, flags.silent, target, flags.reason, f"timed out for {flags.duration}")
            await target.timeout(duration, reason=flags.reason)
        except discord.DiscordException as e:
            await ctx.reply(f"Failed to timeout {target}. {e}", delete_after=10, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.TIMEOUT,
            case_reason=flags.reason,
            case_expires_at=datetime.now(UTC) + duration,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, flags, case, "created", flags.reason, target)

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        flags: TimeoutFlags,
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
        previous_reason: str | None = None,
    ) -> None:
        moderator = ctx.author

        fields = [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if previous_reason:
            fields.append(("Previous Reason", f"> {previous_reason}", False))

        if case is not None:
            embed = await self.create_embed(
                ctx,
                title=f"Case #{case.case_number} {action} ({flags.duration} {case.case_type})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["CASE"],
            )
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case #0 {action} ({flags.duration} {CaseType.TIMEOUT})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.reply(embed=embed, delete_after=10, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Timeout(bot))
