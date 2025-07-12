import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import SnippetBanFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

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
            await ctx.send("User is already snippet banned.", ephemeral=True)
            return

        # Check if moderator has permission to snippet ban the member
        if not await self.check_conditions(ctx, member, ctx.author, "snippet ban"):
            return

        # Execute snippet ban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.SNIPPETBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="snippet banned",
            # Use dummy coroutine for actions that don't need Discord API calls
            actions=[(self._dummy_action(), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(SnippetBan(bot))
