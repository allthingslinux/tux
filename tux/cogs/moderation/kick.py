import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import KickFlags, generate_usage

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
        reason: str | None = None,
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
        reason : str | None
            The reason for the kick.
        flags : KickFlags
            The flags for the command. (silent: bool)

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

        final_reason = reason or self.DEFAULT_REASON

        # Execute kick with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.KICK,
            user=member,
            final_reason=final_reason,
            silent=flags.silent,
            dm_action="kicked",
            actions=[(ctx.guild.kick(member, reason=final_reason), type(None))],
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Kick(bot))
