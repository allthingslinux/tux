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
        *,
        flags: TempBanFlags,
    ) -> None:
        """
        Ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to ban.
        flags : TempBanFlags
            The flags for the command. (reason: str, purge_days: int, silent: bool, expires_at: int The number of days the ban will last for.)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to ban the user.
        discord.HTTPException
            If an error occurs while banning the user.
        """

        if ctx.guild is None:
            logger.warning("Ban command used outside of a guild context.")
            return

        moderator = ctx.author
        duration = parse_time_string(f"{flags.expires_at}d")
        expires_at = datetime.now(UTC) + duration

        if not await self.check_conditions(ctx, member, moderator, "temporarily ban"):
            return

        try:
            await self.send_dm(ctx, flags.silent, member, flags.reason, action="temporarily banned")
            await ctx.guild.ban(member, reason=flags.reason, delete_message_days=flags.purge_days)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to temporarily ban {member}. {e}")
            await ctx.send(f"Failed to temporarily ban {member}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.TEMPBAN,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
            case_expires_at=expires_at,
            case_tempban_expired=False,
        )

        await self.handle_case_response(ctx, CaseType.TEMPBAN, case.case_number, flags.reason, member)

    @tasks.loop(hours=1)
    async def tempban_check(self) -> None:
        # Get all expired tempbans
        expired_temp_bans = await self.db.case.get_expired_tempbans()

        for temp_ban in expired_temp_bans:
            # This make sure that if get_guild doesnt work, we can instead fetch it from the api

            guild = self.bot.get_guild(temp_ban.guild_id)
            if guild is None:
                try:
                    guild = await self.bot.fetch_guild(temp_ban.guild_id)
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(
                        f"Failed to unban user with ID  {temp_ban.case_user_id} | Case number {temp_ban.case_number} | Issue: Failed to get guild with ID {temp_ban.guild_id}. {e}",
                    )
                    return
            else:
                try:
                    # Unban the user by fetching all the bans and if they exist, unban them

                    guild_bans = guild.bans()
                    async for ban_entry in guild_bans:
                        if ban_entry.user.id == temp_ban.case_user_id:
                            await guild.unban(ban_entry.user, reason="Tempban expired")

                            # This just avoids some linting errors
                            assert isinstance(temp_ban.case_number, int)

                            # If the unban goes through, set the tempban as expired and create an untempban case
                            await self.db.case.set_tempban_expired(temp_ban.case_number, temp_ban.guild_id)
                            await self.db.case.insert_case(
                                guild_id=temp_ban.guild_id,
                                case_user_id=temp_ban.case_user_id,
                                case_moderator_id=temp_ban.case_moderator_id,
                                case_type=CaseType.UNTEMPBAN,
                                case_reason="Expired tempban",
                                case_tempban_expired=True,
                            )

                except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
                    logger.error(
                        f"Failed to unban user with ID  {temp_ban.case_user_id} | Case number {temp_ban.case_number} Issue: Failed to unban user. {e}",
                    )
                    return


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempBan(bot))
