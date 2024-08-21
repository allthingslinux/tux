import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.database.controllers.case import CaseController
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.flags import SnippetBanFlags

from . import ModerationCogBase


class SnippetBan(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.case_controller = CaseController()

    @commands.hybrid_command(
        name="snippetban",
        aliases=["sb"],
        usage="snippetban [target]",
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def snippet_ban(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: SnippetBanFlags,
    ) -> None:
        """
        Ban a user from creating snippets.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        target : discord.Member
            The member to snippet ban.
        flags : SnippetBanFlags
            The flags for the command. (reason: str, silent: bool)
        """
        if ctx.guild is None:
            logger.warning("Snippet ban command used outside of a guild context.")
            return

        # Check if the user is already snippet banned
        cases = await self.case_controller.get_all_cases_by_type(ctx.guild.id, CaseType.SNIPPETBAN)
        for case in cases:
            if case.case_target_id == target.id:
                await ctx.send(f"{target.mention} is already snippet banned.", delete_after=10)
                return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.SNIPPETBAN,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.send_dm(ctx, flags.silent, target, flags.reason, "Snippet Banned")
        await self.handle_case_response(ctx, case, "created", flags.reason, target)

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
        previous_reason: str | None = None,
    ) -> None:
        moderator = ctx.author

        fields = [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if previous_reason:
            fields.append(("Previous Reason", f"> {previous_reason}", False))

        if case is not None:
            embed = await self.create_embed(
                ctx,
                title=f"Case #{case.case_number} ({case.case_type}) {action}",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )
            embed.set_thumbnail(url=target.avatar)
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case {action} ({CaseType.SNIPPETBAN})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.send(embed=embed, delete_after=30, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SnippetBan(bot))
