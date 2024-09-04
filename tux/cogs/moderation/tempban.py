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
        )

        await self.handle_case_response(ctx, CaseType.TEMPBAN, case.case_number, flags.reason, member)

    @tasks.loop(minutes=30)
    async def tempban_check(self) -> None:
        # Fetch all guilds and fetch all tempbans for each guild's ID
        guilds = await self.db.guild.get_all_guilds()
        tempbans = [await self.db.case.get_all_cases_by_type(guild.guild_id, CaseType.TEMPBAN) for guild in guilds]
        # Here, we have 3 nested for loops because for some odd reason, tempbans is a list of a list of lists, very confusing ikr

        for tempban in tempbans:
            for cases in tempbans:
                for case in cases:

                    # Check if the case has expired
                    if case.case_expires_at < datetime.now(UTC):
                        # Get the guild, if that doesnt work then fetch it instead

                        guild = self.bot.get_guild(case.guild_id)
                        if guild is None:

                            try:
                                guild = await self.bot.fetch_guild(case.guild_id)

                            except (discord.Forbidden, discord.HTTPException) as e:
                                logger.error(
                                    f"Failed to unban user with ID  {case.case_user_id} | Case number {case.case_number} | Issue: Failed to get guild with ID {case.guild_id}. {e}",
                                )
                                return
                        else:
                            try:
                                # Unban the user

                                guild_bans = guild.bans()
                                async for ban_entry in guild_bans:
                                    if ban_entry.user.id == case.case_user_id:
                                        await guild.unban(ban_entry.user, reason="Tempban expired")

                            except (discord.Forbidden, discord.HTTPException) as e:
                                logger.error(
                                    f"Failed to unban user with ID  {case.case_user_id} | Case number {case.case_number} Issue: Failed to unban user. {e}",
                                )
                                return


async def setup(bot: Tux) -> None:
    await bot.add_cog(TempBan(bot))
