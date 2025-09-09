import discord
from discord.ext import commands

from tux.core.checks import require_moderator
from tux.core.flags import SnippetBanFlags
from tux.core.types import Tux
from tux.database.models import CaseType
from tux.shared.functions import generate_usage

from . import ModerationCogBase


class SnippetBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.snippet_ban.usage = generate_usage(self.snippet_ban, SnippetBanFlags)

    @commands.hybrid_command(
        name="snippetban",
        aliases=["sb"],
    )
    @commands.guild_only()
    @require_moderator()
    async def snippet_ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: SnippetBanFlags,
    ) -> None:
        """
        Ban a member from creating snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to snippet ban.
        flags : SnippetBanFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Check if user is already snippet banned
        if await self.is_snippetbanned(ctx.guild.id, member.id):
            await ctx.reply("User is already snippet banned.", mention_author=False)
            return

        # Permission checks are handled by the @require_moderator() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute snippet ban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=CaseType.SNIPPETBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="snippet banned",
            actions=[],  # No Discord API actions needed for snippet ban
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(SnippetBan(bot))
