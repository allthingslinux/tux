import discord
from discord.ext import commands

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils.constants import Constants as CONST

from . import ModerationCogBase


class Warn(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_group(
        name="warn",
        aliases=["w"],
        usage="$warn <subcommand>",
    )
    @commands.guild_only()
    async def warn(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Warn related commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.

        Raises
        ------
        commands.CommandInvokeError
            If the subcommand is not found.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("warn")

    @warn.command(
        name="create",
        aliases=["c", "add", "a"],
        usage="$warn create [target] [reason]",
    )
    @commands.guild_only()
    async def create_warn(self, ctx: commands.Context[commands.Bot], target: discord.Member, reason: str) -> None:
        """
        Create a warning for a user.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The member to warn.
        reason : str
            The content of the warning.

        Raises
        ------
        commands.MemberNotFound
            If the member is not found.
        """

        if ctx.guild:
            case = await self.db.case.insert_case(
                case_target_id=target.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.WARN,
                case_reason=reason,
                guild_id=ctx.guild.id,
            )

            await self.handle_case_response(ctx, case, "created", reason, target)

    @warn.command(
        name="delete",
        aliases=["d", "remove", "r"],
        usage="$warn delete [case_number]",
    )
    async def delete_warn(self, ctx: commands.Context[commands.Bot], case_number: int) -> None:
        """
        Delete a warning by case number.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case_number : int
            The case number of the warning to delete.

        Raises
        ------
        commands.MemberNotFound
            If the member is not found.
        """

        if ctx.guild:
            case = await self.db.case.get_case_by_case_number_and_guild_id(case_number, ctx.guild.id)

            if not case:
                await ctx.reply("Warning not found.", delete_after=10, ephemeral=True)
                return

            await self.db.case.delete_case_by_case_number_and_guild_id(case_number, ctx.guild.id)

            target = await commands.MemberConverter().convert(ctx, str(case.case_target_id))

            await self.handle_case_response(ctx, case, "deleted", case.case_reason, target)

    @warn.command(
        name="update",
        aliases=["u", "edit", "e", "modify", "m"],
        usage="$warn update [case_number] [reason]",
    )
    async def update_warn(self, ctx: commands.Context[commands.Bot], case_number: int, reason: str) -> None:
        """
        Update a warning by case number.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case_number : int
            The case number of the warning to update.
        reason : str
            The new content of the warning.

        Raises
        ------
        commands.MemberNotFound
            If the member is not found.
        """

        if ctx.guild:
            case = await self.db.case.get_case_by_case_number_and_guild_id(case_number, ctx.guild.id)

            if not case:
                await ctx.reply("Warning not found.", delete_after=10, ephemeral=True)
                return

            previous_reason = case.case_reason
            await self.db.case.update_case_by_case_number_and_guild_id(case_number, ctx.guild.id, reason)

            target = await commands.MemberConverter().convert(ctx, str(case.case_target_id))

            await self.handle_case_response(ctx, case, "updated", reason, target, previous_reason)

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case,
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

        embed = await self.create_embed(
            ctx,
            title=f"Case #{case.case_number} {action} ({case.case_type})",
            fields=fields,
            color=CONST.EMBED_COLORS["CASE"],
            icon_url=CONST.EMBED_ICONS["CASE"],
        )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.reply(embed=embed, delete_after=10, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warn(bot))
