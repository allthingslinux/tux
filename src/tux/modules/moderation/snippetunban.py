import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import require_moderator
from tux.core.flags import SnippetUnbanFlags
from tux.database.models import CaseType

from . import ModerationCogBase


class SnippetUnban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="snippetunban",
        aliases=["sub"],
    )
    @commands.guild_only()
    @require_moderator()
    async def snippet_unban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: SnippetUnbanFlags,
    ) -> None:
        """
        Remove a snippet ban from a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to remove snippet ban from.
        flags : SnippetUnbanFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Check if user is snippet banned
        if not await self.is_snippetbanned(ctx.guild.id, member.id):
            await ctx.reply("User is not snippet banned.", mention_author=False)
            return

        # Execute snippet unban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=CaseType.SNIPPETUNBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="snippet unbanned",
            actions=[],  # No Discord API actions needed for snippet unban
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(SnippetUnban(bot))
