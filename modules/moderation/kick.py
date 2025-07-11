import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.flags import KickFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

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
    @checks.has_pl(2)
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

        # Check if moderator has permission to kick the member
        if not await self.check_conditions(ctx, member, ctx.author, "kick"):
            return

        # Execute kick with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.KICK,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="kicked",
            actions=[(ctx.guild.kick(member, reason=flags.reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Kick(bot))
