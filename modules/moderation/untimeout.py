import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import UntimeoutFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

from . import ModerationCogBase


class Untimeout(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.untimeout.usage = generate_usage(self.untimeout, UntimeoutFlags)

    @commands.hybrid_command(
        name="untimeout",
        aliases=["ut", "uto", "unmute"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
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

        # Check if moderator has permission to untimeout the member
        if not await self.check_conditions(ctx, member, ctx.author, "untimeout"):
            return

        # Execute untimeout with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.UNTIMEOUT,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="removed from timeout",
            actions=[(member.timeout(None, reason=flags.reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Untimeout(bot))
