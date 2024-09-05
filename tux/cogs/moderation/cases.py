import discord
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu

from prisma.enums import CaseType
from prisma.models import Case
from prisma.types import CaseWhereInput
from tux.bot import Tux
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import create_embed_footer
from tux.utils.flags import CaseModifyFlags, CasesViewFlags, generate_usage

from . import ModerationCogBase

emojis: dict[str, int] = {
    "active_case_emoji": 1268115730344443966,
    "inactive_case_emoji": 1268115712627441715,
    "added": 1268115639914987562,
    "removed": 1268116308927713331,
    "ban": 1268115779350560799,
    "kick": 1268115792818470944,
    "timeout": 1268115809083981886,
    "warn": 1268115764498399264,
    "jail": 1268115750392954880,
    "snippetban": 1277174953950576681,
    "snippetunban": 1277174953292337222,
}


class Cases(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.cases_view.usage = generate_usage(self.cases_view, CasesViewFlags)
        self.cases_modify.usage = generate_usage(self.cases_modify, CaseModifyFlags)

    @commands.hybrid_group(
        name="cases",
        aliases=["c"],
        usage="cases <subcommand>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases(self, ctx: commands.Context[Tux]) -> None:
        """
        Manage moderation cases in the server.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("cases")

    @cases.command(
        name="view",
        aliases=["v", "ls", "list"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases_view(
        self,
        ctx: commands.Context[Tux],
        number: int | None,
        *,
        flags: CasesViewFlags,
    ) -> None:
        """
        View moderation cases in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        number : int | None
            The case number to view.
        flags : CasesViewFlags
            The flags for the command. (type, user, moderator)
        """

        assert ctx.guild

        if number is not None:
            await self._view_single_case(ctx, number)
        else:
            await self._view_cases_with_flags(ctx, flags)

    @cases.command(
        name="modify",
        aliases=["m", "edit"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases_modify(
        self,
        ctx: commands.Context[Tux],
        number: int,
        *,
        flags: CaseModifyFlags,
    ) -> None:
        """
        Modify a moderation case in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        number : int
            The case number to modify.
        flags : CaseModifyFlags
            The flags for the command. (status, reason)
        """

        assert ctx.guild

        # If the command is used via prefix, let the user know to use the slash command
        if ctx.message.content.startswith(str(ctx.prefix)):
            await ctx.send("Please use the slash command for this command.", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.get_case_by_number(ctx.guild.id, number)

        if not case:
            await ctx.send("Case not found.", delete_after=30, ephemeral=True)
            return

        if case.case_number is not None:
            await self._update_case(ctx, case, flags)

    async def _view_single_case(
        self,
        ctx: commands.Context[Tux],
        number: int,
    ) -> None:
        """
        View a single case by its number.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        number : int
            The number of the case to view.
        """

        assert ctx.guild

        case = await self.db.case.get_case_by_number(ctx.guild.id, number)
        if not case:
            await ctx.send("Case not found.", delete_after=30)
            return

        user = self.bot.get_user(case.case_user_id)
        if user is None:
            user = await self.bot.fetch_user(case.case_user_id)

        await self._handle_case_response(ctx, case, "viewed", case.case_reason, user)

    async def _view_cases_with_flags(
        self,
        ctx: commands.Context[Tux],
        flags: CasesViewFlags,
    ) -> None:
        """
        View cases with the provided flags.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        flags : CasesViewFlags
            The flags for the command. (type, user, moderator)
        """

        assert ctx.guild

        options: CaseWhereInput = {}

        if flags.type:
            options["case_type"] = flags.type
        if flags.user:
            options["case_user_id"] = flags.user.id
        if flags.moderator:
            options["case_moderator_id"] = flags.moderator.id

        cases = await self.db.case.get_cases_by_options(ctx.guild.id, options)
        total_cases = await self.db.case.get_all_cases(ctx.guild.id)

        if not cases:
            await ctx.send("No cases found.")
            return

        await self._handle_case_list_response(ctx, cases, len(total_cases))

    async def _update_case(
        self,
        ctx: commands.Context[Tux],
        case: Case,
        flags: CaseModifyFlags,
    ) -> None:
        """
        Update a case with the provided flags.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case : Case
            The case to update.
        flags : CaseModifyFlags
            The flags for the command. (status, reason)
        """

        assert ctx.guild

        if case.case_number is None:
            await ctx.send("Failed to update case.", delete_after=30, ephemeral=True)
            return

        updated_case = await self.db.case.update_case(
            ctx.guild.id,
            case.case_number,
            case_reason=flags.reason if flags.reason is not None else case.case_reason,
            case_status=flags.status if flags.status is not None else case.case_status,
        )

        if updated_case is None:
            await ctx.send("Failed to update case.", delete_after=30, ephemeral=True)
            return

        user = await commands.UserConverter().convert(ctx, str(case.case_user_id))

        await self._handle_case_response(ctx, updated_case, "updated", updated_case.case_reason, user)

    async def _handle_case_response(
        self,
        ctx: commands.Context[Tux],
        case: Case | None,
        action: str,
        reason: str,
        user: discord.Member | discord.User,
    ) -> None:
        """
        Handle the response for a case.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case : Case | None
            The case to handle the response for.
        action : str
            The action being performed on the case.
        reason : str
            The reason for the case.
        user : discord.Member | discord.User
            The target of the case.
        """

        if case is not None:
            moderator = ctx.author

            if isinstance(moderator, discord.Member):
                fields = self._create_case_fields(moderator, user, reason)
            else:
                fields = self._create_case_fields(
                    await commands.MemberConverter().convert(ctx, str(case.case_moderator_id)),
                    user,
                    reason,
                )

            embed = self.create_embed(
                ctx,
                title=f"Case #{case.case_number} ({case.case_type}) {action}",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"]
                if case.case_status is True
                else CONST.EMBED_ICONS["INACTIVE_CASE"],
            )
            embed.set_thumbnail(url=user.avatar)
        else:
            embed = discord.Embed(
                title=f"Case {action}",
                description="Failed to find case.",
                color=CONST.EMBED_COLORS["ERROR"],
            )

        await ctx.send(embed=embed, delete_after=30, ephemeral=True)

    async def _handle_case_list_response(
        self,
        ctx: commands.Context[Tux],
        cases: list[Case],
        total_cases: int,
    ) -> None:
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed, all_can_click=True, delete_on_timeout=True)

        if not cases:
            embed = discord.Embed(
                title="Cases",
                description="No cases found.",
                color=CONST.EMBED_COLORS["ERROR"],
            )
            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        cases_per_page = 10
        for i in range(0, len(cases), cases_per_page):
            embed = self._create_case_list_embed(ctx, cases[i : i + cases_per_page], total_cases)
            menu.add_page(embed)

        menu.add_button(
            ViewButton(style=discord.ButtonStyle.secondary, custom_id=ViewButton.ID_GO_TO_FIRST_PAGE, emoji="⏮️"),
        )
        menu.add_button(
            ViewButton(style=discord.ButtonStyle.secondary, custom_id=ViewButton.ID_PREVIOUS_PAGE, emoji="⏪"),
        )
        menu.add_button(ViewButton(style=discord.ButtonStyle.secondary, custom_id=ViewButton.ID_NEXT_PAGE, emoji="⏩"))
        menu.add_button(
            ViewButton(style=discord.ButtonStyle.secondary, custom_id=ViewButton.ID_GO_TO_LAST_PAGE, emoji="⏭️"),
        )

        await menu.start()

    def _create_case_fields(
        self,
        moderator: discord.Member,
        user: discord.Member | discord.User,
        reason: str,
    ) -> list[tuple[str, str, bool]]:
        return [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("User", f"__{user}__\n`{user.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

    def _create_case_list_embed(
        self,
        ctx: commands.Context[Tux],
        cases: list[Case],
        total_cases: int,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=f"Total Cases ({total_cases})",
            description="",
            color=CONST.EMBED_COLORS["CASE"],
        )

        if ctx.guild:
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)

        footer_text, footer_icon_url = create_embed_footer(ctx)
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)

        for case in cases:
            self._add_case_to_embed(embed, case)

        return embed

    def _format_emoji(self, emoji: discord.Emoji | None) -> str:
        return f"<:{emoji.name}:{emoji.id}>" if emoji else ""

    def _get_case_status_emoji(self, case_status: bool | None) -> discord.Emoji | None:
        if case_status is None:
            return None
        return self.bot.get_emoji(emojis["active_case_emoji" if case_status else "inactive_case_emoji"])

    def _get_case_type_emoji(self, case_type: CaseType) -> discord.Emoji | None:
        emoji_map = {
            CaseType.BAN: "ban",
            CaseType.UNBAN: "ban",
            CaseType.KICK: "kick",
            CaseType.TIMEOUT: "timeout",
            CaseType.UNTIMEOUT: "timeout",
            CaseType.WARN: "warn",
            CaseType.JAIL: "jail",
            CaseType.UNJAIL: "jail",
            CaseType.SNIPPETBAN: "snippetban",
            CaseType.SNIPPETUNBAN: "snippetunban",
        }
        emoji_name = emoji_map.get(case_type)
        if emoji_name is not None:
            emoji_id = emojis.get(emoji_name)
            if emoji_id is not None:
                return self.bot.get_emoji(emoji_id)
        return None

    def _get_case_action_emoji(self, case_type: CaseType) -> discord.Emoji | None:
        action = None

        if case_type in [
            CaseType.BAN,
            CaseType.KICK,
            CaseType.TIMEOUT,
            CaseType.WARN,
            CaseType.JAIL,
            CaseType.SNIPPETBAN,
        ]:
            action = "added"
        elif case_type in [CaseType.UNBAN, CaseType.UNTIMEOUT, CaseType.UNJAIL, CaseType.SNIPPETUNBAN]:
            action = "removed"

        if action is not None:
            emoji_id = emojis.get(action)
            if emoji_id is not None:
                return self.bot.get_emoji(emoji_id)
        return None

    def _get_case_description(
        self,
        case: Case,
        case_status_emoji: str,
        case_type_emoji: str,
        case_action_emoji: str,
    ) -> str:
        case_type_and_action = (
            f"{case_action_emoji} {case_type_emoji}"
            if case_action_emoji and case_type_emoji
            else ":interrobang: :interrobang:"
        )
        case_date = discord.utils.format_dt(case.case_created_at, "R") if case.case_created_at else ":interrobang:"

        case_number = f"{case.case_number:04d}" if case.case_number is not None else "0000"

        return f"{case_status_emoji} `{case_number}`\u2002\u2002 {case_type_and_action} \u2002\u2002__{case_date}__\n"

    def _add_case_to_embed(self, embed: discord.Embed, case: Case) -> None:
        case_status_emoji = self._format_emoji(self._get_case_status_emoji(case.case_status))
        case_type_emoji = self._format_emoji(self._get_case_type_emoji(case.case_type))
        case_action_emoji = self._format_emoji(self._get_case_action_emoji(case.case_type))

        if not embed.description:
            embed.description = "**Case**\u2002\u2002\u2002\u2002\u2002**Type**\u2002\u2002\u2002**Date**\n"

        embed.description += self._get_case_description(case, case_status_emoji, case_type_emoji, case_action_emoji)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Cases(bot))
