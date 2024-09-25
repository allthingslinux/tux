import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers.case import CaseController
from tux.utils import checks
from tux.utils.flags import FlagFlags, generate_usage

from . import ModerationCogBase


class Unflag(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.case_controller = CaseController()
        self.flag.usage = generate_usage(self.flag, FlagFlags)

    @commands.hybrid_command(
        name="flag",
        aliases=["fl"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def flag(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: FlagFlags,
    ) -> None:
        """
        Flag a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to flag.
        flags : FlagFlags
            The flags for the command. (reason: str, silent: bool)
        """

        assert ctx.guild

        if await self.is_flagged(ctx.guild.id, member.id):
            await ctx.send("User is already flagged.", delete_after=30, ephemeral=True)
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "flag"):
            return

        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.FLAG,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(
            ctx,
            CaseType.FLAG,
            case.case_number,
            flags.reason,
            member,
            dm_sent=False,
            silent_action=True,
        )

    async def is_flagged(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is flagged.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is flagged, False otherwise.
        """

        flag_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.FLAG)
        unflag_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.UNFLAG)

        flag_count = sum(case.case_user_id == user_id for case in flag_cases)
        unflag_count = sum(case.case_user_id == user_id for case in unflag_cases)

        return flag_count > unflag_count


async def setup(bot: Tux) -> None:
    await bot.add_cog(Unflag(bot))
