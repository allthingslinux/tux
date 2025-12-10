"""Temporary ban moderation commands with automatic expiration handling."""

from __future__ import annotations

import discord
from discord.ext import commands, tasks
from loguru import logger

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import TempBanFlags
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class TempBan(ModerationCogBase):
    """Handles temporary bans with automatic expiration."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the TempBan cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self._processing_tempbans = False
        self.check_tempbans.start()

    @commands.hybrid_command(name="tempban", aliases=["tb"])
    @commands.guild_only()
    @requires_command_permission()
    async def tempban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
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
        flags : TempBanFlags
            The flags for the command. (duration: float (via converter), purge: int (< 7), silent: bool)
        """
        assert ctx.guild

        # Execute tempban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.TEMPBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="temp banned",
            actions=[
                (
                    lambda: ctx.guild.ban(
                        member,
                        reason=flags.reason,
                        delete_message_seconds=flags.purge * 86400,
                    )
                    if ctx.guild
                    else None,
                    type(None),
                ),
            ],
            duration=int(
                flags.duration,
            ),  # Convert float to int for duration in seconds
        )

    async def _process_tempban_case(self, case: Case) -> tuple[int, int]:
        """
        Process an expired tempban case by unbanning the user.

        Returns
        -------
        tuple[int, int]
            (processed_count, failed_count)
        """
        if not (case.guild_id and case.case_user_id and case.id):
            logger.error(f"Invalid case data for case {case.id}")
            return 0, 1

        guild = self.bot.get_guild(case.guild_id)
        if not guild:
            logger.warning(f"Guild {case.guild_id} not found for case {case.id}")
            return 0, 1

        # Check if user is still banned
        try:
            await guild.fetch_ban(discord.Object(id=case.case_user_id))

        except discord.NotFound:
            # User already unbanned - just mark as processed
            logger.info(
                f"User {case.case_user_id} already unbanned, marking case {case.id} as processed",
            )
            await self.db.case.set_tempban_expired(case.id, case.guild_id)
            return 1, 0

        except Exception as e:
            logger.warning(
                f"Error checking ban status for user {case.case_user_id}: {e}",
            )
            # Continue to try unbanning anyway

        # Unban the user
        try:
            await guild.unban(
                discord.Object(id=case.case_user_id),
                reason="Temporary ban expired",
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(
                f"Failed to unban user {case.case_user_id} in guild {guild.id}: {e}",
            )
            return 0, 1
        except Exception as e:
            logger.error(f"Unexpected error processing case {case.id}: {e}")
            return 0, 1
        else:
            await self.db.case.set_tempban_expired(case.id, case.guild_id)
            logger.info(
                f"Unbanned user {case.case_user_id} and marked case {case.id} as processed",
            )
            return 1, 0

    @tasks.loop(minutes=1, name="tempban_checker")
    async def check_tempbans(self) -> None:
        """Check for expired tempbans and unbans the user."""
        if self._processing_tempbans:
            logger.debug("Tempban check is already in progress. Skipping.")
            return

        self._processing_tempbans = True
        try:
            # Collect expired tempbans from all guilds
            all_expired_cases: list[Case] = []
            for guild in self.bot.guilds:
                expired_cases: list[Case] = await self.db.case.get_expired_tempbans(
                    guild.id,
                )
                if expired_cases:
                    logger.info(
                        f"Found {len(expired_cases)} expired tempbans in {guild.name}",
                    )
                    all_expired_cases.extend(expired_cases)

            if not all_expired_cases:
                return

            logger.info(
                f"Processing {len(all_expired_cases)} expired tempban cases.",
            )

            # Process all expired cases
            processed = 0
            failed = 0

            for case in all_expired_cases:
                proc, fail = await self._process_tempban_case(case)
                processed += proc
                failed += fail

            if processed or failed:
                logger.info(
                    f"Finished processing tempbans. Processed: {processed}, Failed: {failed}.",
                )

        finally:
            self._processing_tempbans = False

    @check_tempbans.before_loop
    async def before_check_tempbans(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()

    @check_tempbans.error
    async def on_tempban_error(self, error: BaseException) -> None:
        """Handle errors in the tempban checking loop."""
        logger.error(f"Error in tempban checker loop: {error}")

        if isinstance(error, Exception):
            self.bot.sentry_manager.capture_exception(error)
        else:
            raise error

    async def cog_unload(self) -> None:
        """Cancel the tempban check loop when the cog is unloaded."""
        self.check_tempbans.cancel()


async def setup(bot: Tux) -> None:
    """Set up the TempBan cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(TempBan(bot))
