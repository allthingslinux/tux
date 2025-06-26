from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import TempBanFlags
from tux.utils.functions import generate_usage

from . import ModerationCogBase

if TYPE_CHECKING:
    from tux.bot import Tux


class TempBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.tempban.usage = generate_usage(self.tempban, TempBanFlags)
        self._processing_tempbans = False  # Lock to prevent overlapping task runs
        self.check_tempbans.start()

    @commands.hybrid_command(name="tempban", aliases=["tb"])
    @commands.guild_only()
    @checks.has_pl(3)
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

        # Calculate expiration datetime from duration in seconds
        expires_at = datetime.now(UTC) + timedelta(seconds=flags.duration)

        # Create a simple duration string for logging/display
        # TODO: Implement a more robust human-readable duration formatter
        duration_display_str = str(timedelta(seconds=int(flags.duration)))  # Simple representation

        # Execute tempban with case creation and DM
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.TEMPBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="temp banned",
            actions=[
                (ctx.guild.ban(member, reason=flags.reason, delete_message_seconds=flags.purge * 86400), type(None)),
            ],
            duration=duration_display_str,  # Pass readable string for logging
            expires_at=expires_at,  # Pass calculated expiration datetime
        )

    async def _process_tempban_case(self, case: Case) -> tuple[int, int]:
        """Process an individual tempban case. Returns (processed_cases, failed_cases)."""

        # Check for essential data first
        if not (case.guild_id and case.case_user_id and case.case_id):
            logger.error(f"Invalid case data: {case}")
            return 0, 0

        guild = self.bot.get_guild(case.guild_id)
        if not guild:
            logger.warning(f"Guild {case.guild_id} not found for case {case.case_id}")
            return 0, 0

        # Check ban status
        try:
            await guild.fetch_ban(discord.Object(id=case.case_user_id))
            # If fetch_ban succeeds without error, the user IS banned.
        except discord.NotFound:
            # User is not banned. Mark expired and consider processed.
            await self.db.case.set_tempban_expired(case.case_id, case.guild_id)
            return 1, 0
        except Exception as e:
            # Log error during ban check, but proceed to attempt unban anyway
            # This matches the original logic's behavior.
            logger.warning(f"Error checking ban status for {case.case_user_id} in {guild.id}: {e}")

        # Attempt to unban (runs if user was found banned or if ban check failed)
        processed_count, failed_count = 0, 0
        try:
            # Perform the unban
            await guild.unban(
                discord.Object(id=case.case_user_id),
                reason="Temporary ban expired.",
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            # Discord API unban failed
            logger.error(f"Failed to unban {case.case_user_id} in {guild.id}: {e}")
            failed_count = 1
        except Exception as e:
            # Catch other potential errors during unban
            logger.error(
                f"Unexpected error during unban attempt for tempban {case.case_id} (user {case.case_user_id}, guild {guild.id}): {e}",
            )
            failed_count = 1
        else:
            # Unban successful, now update the database
            try:
                update_result = await self.db.case.set_tempban_expired(case.case_id, case.guild_id)

                if update_result == 1:
                    logger.info(
                        f"Successfully unbanned user {case.case_user_id} and marked case {case.case_id} as expired in guild {guild.id}.",
                    )
                    processed_count = 1
                elif update_result is None:
                    logger.info(
                        f"Successfully unbanned user {case.case_user_id} in guild {guild.id} (case {case.case_id} was already marked expired).",
                    )
                    processed_count = 1  # Still count as success
                else:
                    logger.error(
                        f"Unexpected update result ({update_result}) when marking case {case.case_id} as expired for user {case.case_user_id} in guild {guild.id}.",
                    )
                    failed_count = 1
            except Exception as e:
                # Catch errors during DB update
                logger.error(
                    f"Unexpected error during DB update for tempban {case.case_id} (user {case.case_user_id}, guild {guild.id}): {e}",
                )
                failed_count = 1

        return processed_count, failed_count

    @tasks.loop(minutes=1, name="tempban_checker")
    async def check_tempbans(self) -> None:
        """Checks for expired tempbans and unbans the user."""
        if self._processing_tempbans:
            logger.debug("Tempban check is already in progress. Skipping.")
            return

        self._processing_tempbans = True
        try:
            expired_cases = await self.db.case.get_expired_tempbans()

            if not expired_cases:
                return

            logger.info(f"Processing {len(expired_cases)} expired tempban cases.")

            processed, failed = 0, 0
            for case in expired_cases:
                p, f = await self._process_tempban_case(case)
                processed += p
                failed += f

            if processed or failed:
                logger.info(f"Finished processing tempbans. Processed: {processed}, Failed: {failed}.")

        finally:
            self._processing_tempbans = False

    @check_tempbans.before_loop
    async def before_check_tempbans(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()

    @check_tempbans.error
    async def on_tempban_error(self, error: BaseException) -> None:
        """Handles errors in the tempban checking loop."""
        logger.error(f"Error in tempban checker loop: {error}")

        if isinstance(error, Exception):
            self.bot.sentry_manager.capture_exception(error)
        else:
            raise error

    async def cog_unload(self) -> None:
        self.check_tempbans.cancel()


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempBan(bot))
