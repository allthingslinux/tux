import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import BanFlags, generate_usage

from . import ModerationCogBase


class Ban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.ban.usage = generate_usage(self.ban, BanFlags)

    @commands.hybrid_command(name="ban", aliases=["b"])
    @commands.guild_only()
    @checks.has_pl(3)
    async def ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: BanFlags,
    ) -> None:
        """
        Ban a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
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

        assert ctx.guild

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "ban"):
            return

        try:
            await self.send_dm(ctx, flags.silent, member, flags.reason, action="banned")
            await ctx.guild.ban(member, reason=flags.reason, delete_message_days=flags.purge_days)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to ban {member}. {e}")
            await ctx.send(f"Failed to ban {member}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.BAN,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, CaseType.BAN, case.case_number, flags.reason, member)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Ban(bot))
