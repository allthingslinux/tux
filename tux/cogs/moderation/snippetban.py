import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import SnippetBanFlags, generate_usage

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
    @checks.has_pl(3)
    async def snippet_ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        reason: str | None = None,
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
        reason : str | None
            The reason for the snippet ban.
        flags : SnippetBanFlags
            The flags for the command. (silent: bool)
        """
        assert ctx.guild

        # Check if user is already snippet banned
        if await self.is_snippetbanned(ctx.guild.id, member.id):
            await ctx.send("User is already snippet banned.", ephemeral=True)
            return

        # Check if moderator has permission to snippet ban the member
        if not await self.check_conditions(ctx, member, ctx.author, "snippet ban"):
            return

        final_reason = reason or self.DEFAULT_REASON

        # Execute snippet ban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.SNIPPETBAN,
            user=member,
            final_reason=final_reason,
            silent=flags.silent,
            dm_action="snippet banned",
            # Use dummy coroutine for actions that don't need Discord API calls
            actions=[(self._dummy_action(), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(SnippetBan(bot))
