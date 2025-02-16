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
        reason: str | None = None,
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
        reason : str | None
            The reason for removing the timeout.
        flags : UntimeoutFlags
            The flags for the command. (silent: bool)

        Raises
        ------
        discord.DiscordException
            If an error occurs while removing the timeout.
        """

        assert ctx.guild

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "untimeout"):
            return

        if not member.is_timed_out():
            await ctx.send(f"{member} is not timed out.", ephemeral=True)
            return

        final_reason: str = reason if reason is not None else "No reason provided"
        silent: bool = flags.silent

        try:
            await member.timeout(None, reason=final_reason)

        except discord.DiscordException as e:
            await ctx.send(f"Failed to remove timeout from {member}. {e}", ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNTIMEOUT,
            case_reason=final_reason,
            guild_id=ctx.guild.id,
        )

        dm_sent = await self.send_dm(ctx, silent, member, final_reason, "removed from timeout")

        await self.handle_case_response(
            ctx,
            CaseType.UNTIMEOUT,
            case.case_number,
            final_reason,
            member,
            dm_sent,
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Untimeout(bot))
