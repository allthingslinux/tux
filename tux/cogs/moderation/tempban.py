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
        self._processing_tempbans = False  # Lock to prevent overlapping task runs
        self.tempban_check.start()

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
            The flags for the command. (duration: str, purge: int (< 7), silent: bool)

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

        duration_str = f"{flags.duration}d"

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
            duration=duration_str,
        )

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

            # Get expired tempbans
            expired_cases = await self.db.case.get_expired_tempbans()
            processed_cases = 0
            failed_cases = 0

            for case in expired_cases:
                # Skip cases with missing required data
                if not case.guild_id or not case.case_user_id or not case.case_id:
                    logger.error(f"Invalid case data: {case}")
                    continue

                # Get guild
                guild = self.bot.get_guild(case.guild_id)
                if not guild:
                    logger.warning(f"Guild {case.guild_id} not found for case {case.case_id}")
                    continue  # Skip this case but continue with others

                try:
                    # Verify the user is actually banned before attempting to unban
                    try:
                        ban_entry = await guild.fetch_ban(discord.Object(id=case.case_user_id))
                        if not ban_entry:
                            # User is not banned, just mark as expired
                            await self.db.case.set_tempban_expired(case.case_id, case.guild_id)
                            processed_cases += 1
                            continue
                    except discord.NotFound:
                        # User is not banned, just mark as expired
                        await self.db.case.set_tempban_expired(case.case_id, case.guild_id)
                        processed_cases += 1
                        continue
                    except Exception as e:
                        # On other errors, try to unban anyway
                        logger.warning(f"Error checking ban status for {case.case_user_id} in {guild.id}: {e}")

                    # Unban user
                    await guild.unban(
                        discord.Object(id=case.case_user_id),
                        reason="Temporary ban expired.",
                    )

                    # Set case as expired
                    await self.db.case.set_tempban_expired(case.case_id, case.guild_id)
                    processed_cases += 1

                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"Failed to unban {case.case_user_id} in {guild.id}: {e}")
                    failed_cases += 1
                except Exception as e:
                    logger.error(f"Unexpected error while processing tempban {case.case_id}: {e}")
                    failed_cases += 1

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
