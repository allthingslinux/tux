from datetime import UTC, datetime

import discord
from discord.ext import commands, tasks
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import TempBanFlags, generate_usage
from tux.utils.functions import parse_time_string

from . import ModerationCogBase


class TempBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.tempban.usage = generate_usage(self.tempban, TempBanFlags)
        self.tempban_check.start()

    @commands.hybrid_command(name="tempban", aliases=["tb"])
    @commands.guild_only()
    @checks.has_pl(3)
    async def tempban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        reason: str | None = None,
        *,
        flags: TempBanFlags,
    ) -> None:
        """
        Temporarily ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to ban.
        reason : str | None
            The reason for the ban.
        flags : TempBanFlags
            The flags for the command. (duration: int, purge_days: int (< 7), silent: bool)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to ban the user.
        discord.HTTPException
            If an error occurs while banning the user.
        """

        assert ctx.guild

        await ctx.defer(ephemeral=True)

        if not await self.check_conditions(ctx, member, ctx.author, "temp ban"):
            return

        duration = parse_time_string(f"{flags.expires_at}d")
        expires_at = datetime.now(UTC) + duration
        final_reason: str = reason if reason is not None else "No reason provided"
        silent: bool = flags.silent
        purge_days: int = flags.purge_days

        try:
            dm_sent = await self.send_dm(ctx, silent, member, final_reason, action="temp banned")
            await ctx.guild.ban(member, reason=final_reason, delete_message_days=purge_days)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to temporarily ban {member}. {e}")
            await ctx.send(f"Failed to temporarily ban {member}. {e}", ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.TEMPBAN,
            case_reason=final_reason,
            guild_id=ctx.guild.id,
            case_expires_at=expires_at,
            case_tempban_expired=False,
        )

        await self.handle_case_response(
            ctx,
            CaseType.TEMPBAN,
            case.case_number,
            final_reason,
            member,
            dm_sent,
            f"{flags.expires_at}d",
        )

    @tasks.loop(minutes=1)
    async def tempban_check(self) -> None:
        """Check for expired tempbans."""
        try:
            expired_cases = await self.db.case.get_expired_tempbans()
            for case in expired_cases:
                guild = self.bot.get_guild(case.guild_id)
                if not guild:
                    continue

                try:
                    await guild.unban(
                        discord.Object(id=case.case_user_id),
                        reason="Temporary ban expired.",
                    )
                    await self.db.case.set_tempban_expired(case.case_id, case.guild_id)

                except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
                    logger.error(f"Failed to unban {case.case_user_id} in {guild.id}. {e}")

        except Exception as e:
            logger.error(f"Failed to check tempbans. {e}")

    @tempban_check.before_loop
    async def before_tempban_check(self) -> None:
        """Wait for the bot to be ready before starting the loop."""
        await self.bot.wait_until_ready()

    async def cog_unload(self) -> None:
        """Cancel the tempban check loop when the cog is unloaded."""
        self.tempban_check.cancel()


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempBan(bot))
