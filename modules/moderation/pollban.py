import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import PollBanFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

from . import ModerationCogBase


class PollBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.poll_ban.usage = generate_usage(self.poll_ban, PollBanFlags)

    @commands.hybrid_command(
        name="pollban",
        aliases=["pb"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
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
            await ctx.send("User is already poll banned.", ephemeral=True)
            return

        # Check if moderator has permission to poll ban the member
        if not await self.check_conditions(ctx, member, ctx.author, "poll ban"):
            return

        # Execute poll ban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.POLLBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="poll banned",
            # Use dummy coroutine for actions that don't need Discord API calls
            actions=[(self._dummy_action(), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(PollBan(bot))
