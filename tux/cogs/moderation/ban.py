import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.utils import checks
from tux.utils.flags import BanFlags

from . import ModerationCogBase


class Ban(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="ban",
        aliases=["b"],
        usage="ban [target] [reason] <purge_days> <silent>",
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def ban(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: BanFlags,
    ) -> None:
        """
        Ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The member to ban.
        flags : BanFlags
            The flags for the command. (reason: str, purge_days: int (< 7), silent: bool)

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

        if not await self.check_conditions(ctx, target, moderator, "ban"):
            return

        try:
            await self.send_dm(ctx, flags.silent, target, flags.reason, action="banned")
            await ctx.guild.ban(target, reason=flags.reason, delete_message_days=flags.purge_days)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to ban {target}. {e}")
            await ctx.send(f"Failed to ban {target}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.BAN,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, CaseType.BAN, case.case_id, flags.reason, target)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
