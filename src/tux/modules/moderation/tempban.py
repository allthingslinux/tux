# Removed unused datetime imports

import discord
from discord.ext import commands, tasks
from loguru import logger

from tux.core.bot import Tux
from tux.core.checks import require_moderator
from tux.core.flags import TempBanFlags
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType
from tux.shared.functions import generate_usage

from . import ModerationCogBase


class TempBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.tempban.usage = generate_usage(self.tempban, TempBanFlags)
        self._processing_tempbans = False  # Lock to prevent overlapping task runs
        self.tempban_check.start()

    @commands.hybrid_command(name="tempban", aliases=["tb"])
    @commands.guild_only()
    @require_moderator()
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

        # Permission checks are handled by the @require_moderator() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Execute tempban with case creation and DM
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.TEMPBAN,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="temp banned",
            actions=[
                (ctx.guild.ban(member, reason=flags.reason, delete_message_seconds=flags.purge * 86400), type(None)),
            ],
            duration=int(flags.duration),  # Convert float to int for duration in seconds
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
                elif not update_result:
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

    @tasks.loop(minutes=1)
    async def tempban_check(self) -> None:
        """
        Check for expired tempbans at a set interval and unban the user if the ban has expired.

        Uses a simple locking mechanism to prevent overlapping executions.
        Processes bans in smaller batches to prevent timeout issues.

        Raises
        ------
        Exception
            If an error occurs while checking for expired tempbans.
        """
        # Skip if already processing
        if self._processing_tempbans:
            return

        try:
            self._processing_tempbans = True

            # Get expired tempbans - need to get from all guilds since this is a task loop
            # For now, get from a default guild or implement guild-specific logic
            expired_cases = await self.db.case.get_expired_tempbans(0)  # TODO: Implement proper guild handling
            processed_cases = 0
            failed_cases = 0

            for case in expired_cases:
                # Process each case using the helper method
                processed, failed = await self._process_tempban_case(case)
                processed_cases += processed
                failed_cases += failed

            if processed_cases > 0 or failed_cases > 0:
                logger.info(f"Tempban check: processed {processed_cases} cases, {failed_cases} failures")

        except Exception as e:
            logger.error(f"Failed to check tempbans: {e}")
        finally:
            self._processing_tempbans = False

    @tempban_check.before_loop
    async def before_tempban_check(self) -> None:
        """Wait for the bot to be ready before starting the loop."""
        await self.bot.wait_until_ready()

    async def cog_unload(self) -> None:
        """Cancel the tempban check loop when the cog is unloaded."""
        self.tempban_check.cancel()


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempBan(bot))
