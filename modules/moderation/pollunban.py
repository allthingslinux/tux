import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import PollUnbanFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

from . import ModerationCogBase


class PollUnban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.poll_unban.usage = generate_usage(self.poll_unban, PollUnbanFlags)

    @commands.hybrid_command(
        name="pollunban",
        aliases=["pub"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
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
            await ctx.send("User is not poll banned.", ephemeral=True)
            return

        # Check if moderator has permission to poll unban the member
        if not await self.check_conditions(ctx, member, ctx.author, "poll unban"):
            return

        # Execute poll unban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.POLLUNBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="poll unbanned",
            # Use dummy coroutine for actions that don't need Discord API calls
            actions=[(self._dummy_action(), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(PollUnban(bot))
