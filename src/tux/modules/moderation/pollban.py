import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import require_moderator
from tux.core.flags import PollBanFlags
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class PollBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="pollban",
        aliases=["pb"],
    )
    @commands.guild_only()
    @require_moderator()
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

        # Permission checks are handled by the @require_moderator() decorator
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
    await bot.add_cog(PollBan(bot))
