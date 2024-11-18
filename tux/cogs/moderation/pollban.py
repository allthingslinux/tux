import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers.case import CaseController
from tux.utils import checks
from tux.utils.flags import PollBanFlags, generate_usage

from . import ModerationCogBase


class PollBan(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.case_controller = CaseController()
        self.poll_ban.usage = generate_usage(self.poll_ban, PollBanFlags)

    @commands.hybrid_command(
        name="pollban",
        aliases=["pb"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def poll_ban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: PollBanFlags,
    ) -> None:
        """
        Ban a user from creating polls using tux.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to poll ban.
        flags : PollBanFlags
            The flags for the command. (reason: str, silent: bool)
        """

        assert ctx.guild
        await ctx.defer(ephemeral=True)

        if await self.is_pollbanned(ctx.guild.id, member.id):
            await ctx.send("User is already poll banned.", ephemeral=True)
            return

        try:
            case = await self.db.case.insert_case(
                case_user_id=member.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.POLLBAN,
                case_reason=flags.reason,
                guild_id=ctx.guild.id,
            )

        except Exception as e:
            logger.error(f"Failed to ban {member}. {e}")
            await ctx.send(f"Failed to ban {member}. {e}", ephemeral=True)
            return

        dm_sent = await self.send_dm(ctx, flags.silent, member, flags.reason, "poll banned")
        await self.handle_case_response(ctx, CaseType.POLLBAN, case.case_number, flags.reason, member, dm_sent)


async def setup(bot: Tux) -> None:
    await bot.add_cog(PollBan(bot))
