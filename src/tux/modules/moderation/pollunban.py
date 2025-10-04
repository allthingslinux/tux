import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import PollUnbanFlags
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class PollUnban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="pollunban",
        aliases=["pub"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def poll_unban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: PollUnbanFlags,
    ) -> None:
        """
        Remove a poll ban from a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to remove poll ban from.
        flags : PollUnbanFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Check if user is poll banned
        if not await self.is_pollbanned(ctx.guild.id, member.id):
            await ctx.reply("User is not poll banned.", mention_author=False)
            return

        # Permission checks are handled by the @requires_command_permission() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute poll unban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.POLLUNBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="poll unbanned",
            actions=[],  # No Discord API actions needed for poll unban
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(PollUnban(bot))
