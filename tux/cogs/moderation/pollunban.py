import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers.case import CaseController
from tux.utils import checks
from tux.utils.flags import PollUnbanFlags, generate_usage

from . import ModerationCogBase


class PollUnban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.case_controller = CaseController()
        self.poll_unban.usage = generate_usage(self.poll_unban, PollUnbanFlags)

    @commands.hybrid_command(
        name="pollunban",
        aliases=["pub"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def poll_unban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: PollUnbanFlags,
    ):
        """
        Unban a user from creating snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to snippet unban.
        flags : PollUnbanFlags
            The flags for the command. (reason: str, silent: bool)
        """

        assert ctx.guild
        await ctx.defer(ephemeral=True)

        if not await self.is_pollbanned(ctx.guild.id, member.id):
            await ctx.send("User is not poll banned.", ephemeral=True)
            return

        try:
            case = await self.db.case.insert_case(
                case_user_id=member.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.POLLUNBAN,
                case_reason=flags.reason,
                guild_id=ctx.guild.id,
            )

        except Exception as e:
            logger.error(f"Failed to poll unban {member}. {e}")
            await ctx.send(f"Failed to poll unban {member}. {e}", ephemeral=True)
            return

        dm_sent = await self.send_dm(ctx, flags.silent, member, flags.reason, "poll unbanned")
        await self.handle_case_response(ctx, CaseType.POLLUNBAN, case.case_number, flags.reason, member, dm_sent)


async def setup(bot: Tux) -> None:
    await bot.add_cog(PollUnban(bot))
