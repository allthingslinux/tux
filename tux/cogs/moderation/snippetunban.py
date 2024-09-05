import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers.case import CaseController
from tux.utils import checks
from tux.utils.flags import SnippetUnbanFlags, generate_usage

from . import ModerationCogBase


class SnippetUnban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.case_controller = CaseController()
        self.snippet_unban.usage = generate_usage(self.snippet_unban, SnippetUnbanFlags)

    @commands.hybrid_command(
        name="snippetunban",
        aliases=["sub"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def snippet_unban(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: SnippetUnbanFlags,
    ):
        """
        Unban a user from creating snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        member : discord.Member
            The member to snippet unban.
        flags : SnippetUnbanFlags
            The flags for the command. (reason: str, silent: bool)
        """

        assert ctx.guild

        if not await self.is_snippetbanned(ctx.guild.id, member.id):
            await ctx.send("User is not snippet banned.", delete_after=30, ephemeral=True)
            return

        try:
            case = await self.db.case.insert_case(
                case_user_id=member.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.SNIPPETUNBAN,
                case_reason=flags.reason,
                guild_id=ctx.guild.id,
            )

        except Exception as e:
            logger.error(f"Failed to snippet unban {member}. {e}")
            await ctx.send(f"Failed to snippet unban {member}. {e}", delete_after=30, ephemeral=True)
            return

        await self.send_dm(ctx, flags.silent, member, flags.reason, "snippet unbanned")
        await self.handle_case_response(ctx, CaseType.SNIPPETUNBAN, case.case_number, flags.reason, member)

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is snippet banned.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is snippet banned, False otherwise.
        """

        ban_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.SNIPPETBAN)
        unban_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.SNIPPETUNBAN)

        ban_count = sum(case.case_user_id == user_id for case in ban_cases)
        unban_count = sum(case.case_user_id == user_id for case in unban_cases)

        return ban_count > unban_count


async def setup(bot: Tux) -> None:
    await bot.add_cog(SnippetUnban(bot))
