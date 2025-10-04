import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import WarnFlags
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class Warn(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="warn",
        aliases=["w"],
    )
    @commands.guild_only()
    @requires_command_permission()
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

        # Execute warn with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.WARN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="warned",
            actions=[],  # No Discord API actions needed for warnings
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Warn(bot))
