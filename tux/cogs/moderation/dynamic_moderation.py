"""
Dynamic moderation command system demonstration.

This module demonstrates how moderation commands can be implemented
using a unified approach with the mixed_args system.
"""

import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.mixed_args import generate_mixed_usage, parse_mixed_arguments

from . import ModerationCogBase


class DynamicModerationCog(ModerationCogBase):
    """
    Dynamic moderation cog that demonstrates the unified approach.

    This cog shows how moderation commands can be implemented
    using the mixed_args system for consistent argument parsing.
    """

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Set usage string for dtimeout command
        self.dtimeout.usage = generate_mixed_usage("dtimeout", ["member"], ["duration", "reason"], ["-d", "-s"])

    @commands.hybrid_command(
        name="dtimeout",
        aliases=["dt", "dto", "dmute", "dm"],
        description="Dynamic timeout command using mixed_args",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def dtimeout(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        mixed_args: str = "",
    ) -> None:
        """
        Timeout a member using dynamic mixed arguments.

        Supports both positional and flag-based arguments:
        - Positional: `dtimeout @user 14d reason`
        - Flag-based: `dtimeout @user reason -d 14d`
        - Mixed: `dtimeout @user 14d reason -s`
        """
        assert ctx.guild

        # Check if member is already timed out
        if member.is_timed_out():
            await ctx.send(f"{member} is already timed out.", ephemeral=True)
            return

        # Check if moderator has permission to timeout the member
        if not await self.check_conditions(ctx, member, ctx.author, "timeout"):
            return

        # Parse mixed arguments
        parsed_args = parse_mixed_arguments(mixed_args)

        # Extract values with defaults
        duration = parsed_args.get("duration")
        reason = parsed_args.get("reason", "No reason provided")
        silent = parsed_args.get("silent", False)

        # Validate that we have a duration
        if not duration:
            await ctx.send("Please provide a duration for the timeout.", ephemeral=True)
            return

        # Execute the timeout action
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.TIMEOUT,
            user=member,
            reason=reason,
            silent=silent,
            dm_action="timed out",
            actions=[
                (member.timeout(duration, reason=reason), type(None)),
            ],
        )


async def setup(bot: Tux) -> None:
    """Set up the dynamic moderation cog."""
    await bot.add_cog(DynamicModerationCog(bot))
