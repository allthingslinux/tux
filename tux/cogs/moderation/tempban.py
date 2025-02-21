import discord
from discord.ext import commands, tasks
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import TempBanFlags, generate_usage

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

        # Check if moderator has permission to temp ban the member
        if not await self.check_conditions(ctx, member, ctx.author, "temp ban"):
            return

        final_reason = reason or self.DEFAULT_REASON
        duration_str = f"{flags.expires_at}d"

        # Execute tempban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.TEMPBAN,
            user=member,
            final_reason=final_reason,
            silent=flags.silent,
            dm_action="temp banned",
            actions=[(ctx.guild.ban(member, reason=final_reason, delete_message_days=flags.purge_days), type(None))],
            duration=duration_str,
        )

    @tasks.loop(minutes=1)
    async def tempban_check(self) -> None:
        """
        Check for expired tempbans at a set interval and unban the user if the ban has expired.

        Raises
        ------
        Exception
            If an error occurs while checking for expired tempbans.
        """

        try:
            # Get expired tempbans
            expired_cases = await self.db.case.get_expired_tempbans()

            for case in expired_cases:
                # Get guild
                guild = self.bot.get_guild(case.guild_id)
                if not guild:
                    continue

                try:
                    # Unban user
                    await guild.unban(
                        discord.Object(id=case.case_user_id),
                        reason="Temporary ban expired.",
                    )

                    # Set case as expired
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
