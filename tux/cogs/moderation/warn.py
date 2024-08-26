import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.utils import checks
from tux.utils.flags import WarnFlags, generate_usage

from . import ModerationCogBase


class Warn(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.warn.usage = generate_usage(self.warn, WarnFlags)

    @commands.hybrid_command(
        name="warn",
        aliases=["w"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def warn(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: WarnFlags,
    ) -> None:
        """
        Warn a member from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The member to warn.
        flags : WarnFlags
            The flags for the command. (reason: str, silent: bool)
        """

        if ctx.guild is None:
            logger.warning("Warn command used outside of a guild context.")
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, target, moderator, "warn"):
            return

        await self.send_dm(ctx, flags.silent, target, flags.reason, "warned")

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.WARN,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, CaseType.WARN, case.case_id, flags.reason, target)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warn(bot))
