"""Poll ban moderation command.

This module provides functionality to ban Discord members from creating
polls. It integrates with the moderation case tracking system.
"""

import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import PollBanFlags
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class PollBan(ModerationCogBase):
    """Discord cog for poll ban moderation commands.

    This cog provides the pollban command which prevents members from
    creating polls in the server.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the PollBan cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="pollban",
        aliases=["pb"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def poll_ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: PollBanFlags,
    ) -> None:
        """
        Ban a user from creating polls.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to poll ban.
        flags : PollBanFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Check if user is already poll banned
        if await self.is_pollbanned(ctx.guild.id, member.id):
            await ctx.reply("User is already poll banned.", mention_author=False)
            return

        # Permission checks are handled by the @requires_command_permission() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute poll ban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.POLLBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="poll banned",
            actions=[],  # No Discord API actions needed for poll ban
        )


async def setup(bot: Tux) -> None:
    """Set up the PollBan cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(PollBan(bot))
