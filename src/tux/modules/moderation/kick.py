import discord
from discord.ext import commands

from tux.core.checks import require_junior_mod
from tux.core.flags import KickFlags
from tux.core.types import Tux
from tux.database.models import CaseType as DBCaseType
from tux.shared.functions import generate_usage

from . import ModerationCogBase


class Kick(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.kick.usage = generate_usage(self.kick, KickFlags)

    @commands.hybrid_command(
        name="kick",
        aliases=["k"],
    )
    @commands.guild_only()
    @require_junior_mod()
    async def kick(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: KickFlags,
    ) -> None:
        """
        Kick a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to kick.
        flags : KickFlags
            The flags for the command. (reason: str, silent: bool)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to kick the user.
        discord.HTTPException
            If an error occurs while kicking the user.
        """
        assert ctx.guild

        # Permission checks are handled by the @require_moderator() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute kick with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.KICK,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="kicked",
            actions=[(member.kick(reason=flags.reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Kick(bot))
