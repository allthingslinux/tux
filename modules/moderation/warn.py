import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import WarnFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

from . import ModerationCogBase


class Warn(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.warn.usage = generate_usage(self.warn, WarnFlags)

    @commands.hybrid_command(
        name="warn",
        aliases=["w"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def warn(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: WarnFlags,
    ) -> None:
        """
        Warn a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to warn.
        flags : WarnFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Check if moderator has permission to warn the member
        if not await self.check_conditions(ctx, member, ctx.author, "warn"):
            return

        # Execute warn with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.WARN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="warned",
            # Use dummy coroutine for actions that don't need Discord API calls
            actions=[(self._dummy_action(), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Warn(bot))
