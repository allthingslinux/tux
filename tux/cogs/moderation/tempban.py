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
        Temporarily ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to ban.
        flags : TempBanFlags
            The flags for the command. (reason: str, silent: bool, expires_at: int, purge_days: int)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to ban the user.
        discord.HTTPException
            If an error occurs while banning the user.
        """

        assert ctx.guild

        if not await self.check_conditions(ctx, member, ctx.author, "temp ban"):
            return

        duration = parse_time_string(f"{flags.expires_at}d")
        expires_at = datetime.now(UTC) + duration

        try:
            dm_sent = await self.send_dm(ctx, flags.silent, member, flags.reason, action="temp banned")
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

        await self.handle_case_response(
            ctx,
            CaseType.TEMPBAN,
            case.case_number,
            flags.reason,
            member,
            dm_sent,
            silent_action=False,
        )

    @tasks.loop(hours=1)
    async def tempban_check(self) -> None:
        expired_temp_bans = await self.db.case.get_expired_tempbans()

        for temp_ban in expired_temp_bans:
            # Get the guild from the cache or fetch it from the API
            guild = self.bot.get_guild(temp_ban.guild_id) or await self.bot.fetch_guild(temp_ban.guild_id)
            if not guild:
                logger.error(f"Failed to get guild with ID {temp_ban.guild_id} for tempban check.")
                continue

            try:
                ban_entry = await guild.fetch_ban(discord.Object(id=temp_ban.case_user_id))

                await guild.unban(ban_entry.user, reason=f"Tempban expired | Case number: {temp_ban.case_number}")

                await self.db.case.set_tempban_expired(temp_ban.case_number, temp_ban.guild_id)

                await self.db.case.insert_case(
                    guild_id=temp_ban.guild_id,
                    case_user_id=temp_ban.case_user_id,
                    case_moderator_id=temp_ban.case_moderator_id,
                    case_type=CaseType.UNTEMPBAN,
                    case_reason="Expired tempban",
                    case_tempban_expired=True,
                )

                logger.debug(f"Unbanned user with ID {temp_ban.case_user_id} | Case number {temp_ban.case_number}")

            except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
                logger.error(
                    f"Failed to unban user with ID {temp_ban.case_user_id} | Case number {temp_ban.case_number}. Error: {e}",
                )


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempBan(bot))
