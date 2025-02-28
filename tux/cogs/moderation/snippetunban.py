import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import SnippetUnbanFlags, generate_usage

from . import ModerationCogBase


class SnippetUnban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.snippet_unban.usage = generate_usage(self.snippet_unban, SnippetUnbanFlags)

    @commands.hybrid_command(
        name="snippetunban",
        aliases=["sub"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def snippet_unban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        reason: str | None = None,
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
        reason : str | None
            The reason for removing the snippet ban.
        flags : SnippetUnbanFlags
            The flags for the command. (silent: bool)
        """
        assert ctx.guild

        # Check if user is snippet banned
        if not await self.is_snippetbanned(ctx.guild.id, member.id):
            await ctx.send("User is not snippet banned.", ephemeral=True)
            return

        # Check if moderator has permission to snippet unban the member
        if not await self.check_conditions(ctx, member, ctx.author, "snippet unban"):
            return

        final_reason = reason or self.DEFAULT_REASON

        # Execute snippet unban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.SNIPPETUNBAN,
            user=member,
            final_reason=final_reason,
            silent=flags.silent,
            dm_action="snippet unbanned",
            # Use dummy coroutine for actions that don't need Discord API calls
            actions=[(self._dummy_action(), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(SnippetUnban(bot))
