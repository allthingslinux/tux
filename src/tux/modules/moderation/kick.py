"""
Kick moderation command for Tux Bot.

This module provides the kick command functionality, allowing server
moderators to kick users from the server.
"""

import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import KickFlags
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class Kick(ModerationCogBase):
    """Kick command cog for moderating server members."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Kick cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the cog with.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="kick",
        aliases=["k"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def kick(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: KickFlags,
    ) -> None:
        """
        Kick a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to kick.
        flags : KickFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Permission checks are handled by the @requires_command_permission() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute kick with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.KICK,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="kicked",
            actions=[(lambda: member.kick(reason=flags.reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    """Set up the Kick cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Kick(bot))
