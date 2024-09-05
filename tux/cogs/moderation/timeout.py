from datetime import UTC, datetime

import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import TimeoutFlags, generate_usage
from tux.utils.functions import parse_time_string

from . import ModerationCogBase


class Timeout(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.timeout.usage = generate_usage(self.timeout, TimeoutFlags)

    @commands.hybrid_command(
        name="timeout",
        aliases=["t", "to", "mute"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def timeout(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: TimeoutFlags,
    ) -> None:
        """
        Timeout a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to timeout.
        flags : TimeoutFlags
            The flags for the command (duration: str, reason: str, silent: bool).

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """

        assert ctx.guild

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "timeout"):
            return

        if member.is_timed_out():
            await ctx.send(f"{member} is already timed out.", delete_after=30, ephemeral=True)
            return

        duration = parse_time_string(flags.duration)

        try:
            await member.timeout(duration, reason=flags.reason)

        except discord.DiscordException as e:
            await ctx.send(f"Failed to timeout {member}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.TIMEOUT,
            case_reason=flags.reason,
            case_expires_at=datetime.now(UTC) + duration,
            guild_id=ctx.guild.id,
        )

        await self.send_dm(ctx, flags.silent, member, flags.reason, f"timed out for {flags.duration}")
        await self.handle_case_response(ctx, CaseType.TIMEOUT, case.case_number, flags.reason, member, flags.duration)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Timeout(bot))
