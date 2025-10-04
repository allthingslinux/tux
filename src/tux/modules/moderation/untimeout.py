import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import UntimeoutFlags
from tux.database.models import CaseType as DBCaseType
from tux.shared.functions import generate_usage

from . import ModerationCogBase


class Untimeout(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.untimeout.usage = generate_usage(self.untimeout, UntimeoutFlags)

    @commands.hybrid_command(
        name="untimeout",
        aliases=["uto", "unmute"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def untimeout(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: UntimeoutFlags,
    ) -> None:
        """
        Remove timeout from a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to remove timeout from.
        flags : UntimeoutFlags
            The flags for the command. (reason: str, silent: bool)

        Raises
        ------
        discord.DiscordException
            If an error occurs while removing the timeout.
        """
        assert ctx.guild

        # Check if member is timed out
        if not member.is_timed_out():
            await ctx.send(f"{member} is not timed out.", ephemeral=True)
            return

        # Execute untimeout with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.UNTIMEOUT,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="removed from timeout",
            actions=[(lambda: member.timeout(None, reason=flags.reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Untimeout(bot))
