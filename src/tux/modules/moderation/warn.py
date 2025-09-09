import discord
from discord.ext import commands

from tux.core.checks import require_junior_mod
from tux.core.flags import WarnFlags
from tux.core.types import Tux
from tux.database.models import CaseType as DBCaseType
from tux.shared.functions import generate_usage

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
    @require_junior_mod()
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

        # Permission checks are handled by the @require_moderator() decorator
        # Additional validation will be handled by the ModerationCoordinator service

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
