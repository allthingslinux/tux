import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import UntimeoutFlags, generate_usage

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
        Untimeout a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to untimeout.
        flags : UntimeoutFlags
            The flags for the command (reason: str, silent: bool).

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """

        assert ctx.guild

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "untimeout"):
            return

        if not member.is_timed_out():
            await ctx.send(f"{member} is not currently timed out.", delete_after=30, ephemeral=True)

        try:
            # By passing `None` as the duration, the timeout is removed
            await member.timeout(None, reason=flags.reason)
        except discord.DiscordException as e:
            await ctx.send(f"Failed to untimeout {member}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNTIMEOUT,
            case_reason=flags.reason,
            case_expires_at=None,
            guild_id=ctx.guild.id,
        )

        await self.send_dm(ctx, flags.silent, member, flags.reason, "untimed out")
        await self.handle_case_response(ctx, CaseType.UNTIMEOUT, case.case_number, flags.reason, member)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Untimeout(bot))
