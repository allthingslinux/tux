import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

import tux.utils.checks as checks
from prisma.enums import CaseType
from prisma.models import Case
from prisma.types import CaseWhereInput
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import create_embed_footer
from tux.utils.flags import CaseModifyFlags, CasesViewFlags

from . import ModerationCogBase

# active_case_emoji, inactive_case_emoji = (1265754900533608509, 1265754928610279495)

emojis = {
    "active_case_emoji": 1268115730344443966,
    "inactive_case_emoji": 1268115712627441715,
    "added": 1268115639914987562,
    "removed": 1268116308927713331,
    "ban": 1268115779350560799,
    "kick": 1268115792818470944,
    "timeout": 1268115809083981886,
    "warn": 1268115764498399264,
    "jail": 1268115750392954880,
}

# case_type_emojis = {
#     CaseType.BAN: emojis["added"] + emojis["ban"],
#     CaseType.UNBAN: emojis["removed"] + emojis["ban"],
#     CaseType.KICK: emojis["added"] + emojis["kick"],
#     CaseType.TIMEOUT: emojis["added"] + emojis["timeout"],
#     CaseType.UNTIMEOUT: emojis["removed"] + emojis["timeout"],
#     CaseType.WARN: emojis["added"] + emojis["warn"],
#     CaseType.JAIL: emojis["added"] + emojis["jail"],
#     CaseType.UNJAIL: emojis["removed"] + emojis["jail"],
# }

# we need to define each case type to an action emoji and a case type emoji and they need to be seperated by a space

# case_type_emojis = {
#     CaseType.BAN: f"{emojis['added']} {emojis['ban']}",
#     CaseType.UNBAN: f"{emojis['removed']} {emojis['ban']}",
#     CaseType.KICK: f"{emojis['added']} {emojis['kick']}",
#     CaseType.TIMEOUT: f"{emojis['added']} {emojis['timeout']}",
#     CaseType.UNTIMEOUT: f"{emojis['removed']} {emojis['timeout']}",
#     CaseType.WARN: f"{emojis['added']} {emojis['warn']}",
#     CaseType.JAIL: f"{emojis['added']} {emojis['jail']}",
#     CaseType.UNJAIL: f"{emojis['removed']} {emojis['jail']}",
# }


class Cases(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_group(
        name="cases",
        aliases=["c"],
        usage="$cases <subcommand>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Manage moderation cases in the server.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("cases")

    @cases.command(
        name="view",
        aliases=["v", "ls", "list"],
        usage="$cases view <case_number> <flags>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases_view(
        self,
        ctx: commands.Context[commands.Bot],
        case_number: int | None,
        flags: CasesViewFlags,
    ) -> None:
        """
        View moderation cases in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case_number : int | None
            The case number to view.
        flags : CasesViewFlags
            The flags for the command. (type, target, moderator)
        """

        if ctx.guild is None:
            logger.warning("Cases view command used outside of a guild context.")
            return

        if case_number is not None:
            await self._view_single_case(ctx, case_number)
        else:
            await self._view_cases_with_flags(ctx, flags)

    @cases.command(
        name="modify",
        aliases=["m", "edit"],
        usage="$cases modify [case_number] <flags>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases_modify(
        self,
        ctx: commands.Context[commands.Bot],
        case_number: int,
        flags: CaseModifyFlags,
    ) -> None:
        """
        Modify a moderation case in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case_number : int
            The case number to modify.
        flags : CaseModifyFlags
            The flags for the command. (status, reason)
        """

        if ctx.guild is None:
            logger.warning("Cases modify command used outside of a guild context.")
            return

        # If the command is used via prefix, let the user know to use the slash command
        if ctx.message.content.startswith(str(ctx.prefix)):
            await ctx.reply("Please use the slash command for this command.", delete_after=10, ephemeral=True)
            return

        case = await self.db.case.get_case_by_number(ctx.guild.id, case_number)

        if not case:
            await ctx.reply("Case not found.", delete_after=10, ephemeral=True)
            return

        if case.case_number is not None:
            await self._update_case(ctx, case, flags)

    async def _view_single_case(
        self,
        ctx: commands.Context[commands.Bot],
        case_number: int,
    ) -> None:
        """
        View a single case by its number.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case_number : int
            The number of the case to view.
        """

        if ctx.guild is None:
            logger.warning("Cases view command used outside of a guild context.")
            return

        case = await self.db.case.get_case_by_number(ctx.guild.id, case_number)
        if not case:
            await ctx.reply("Case not found.", delete_after=10)
            return

        target = await commands.MemberConverter().convert(ctx, str(case.case_target_id))
        await self._handle_case_response(ctx, case, "viewed", case.case_reason, target)

    async def _view_cases_with_flags(
        self,
        ctx: commands.Context[commands.Bot],
        flags: CasesViewFlags,
    ) -> None:
        """
        View cases with the provided flags.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        flags : CasesViewFlags
            The flags for the command. (type, target, moderator)
        """

        if ctx.guild is None:
            logger.warning("Cases view command used outside of a guild context.")
            return

        options: CaseWhereInput = {}

        if flags.type:
            options["case_type"] = flags.type
        if flags.target:
            options["case_target_id"] = flags.target.id
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
        ctx: commands.Context[commands.Bot],
        case: Case,
        flags: CaseModifyFlags,
    ) -> None:
        """
        Update a case with the provided flags.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case : Case
            The case to update.
        flags : CaseModifyFlags
            The flags for the command. (status, reason)
        """

        if ctx.guild is None:
            logger.warning("Cases modify command used outside of a guild context.")
            return

        if case.case_number is None:
            await ctx.reply("Failed to update case.", delete_after=10)
            return

        updated_case = await self.db.case.update_case(
            ctx.guild.id,
            case.case_number,
            case_reason=flags.reason if flags.reason is not None else case.case_reason,
            case_status=flags.status if flags.status is not None else case.case_status,
        )

        if updated_case is None:
            await ctx.reply("Failed to update case.", delete_after=10)
            return

        target = await commands.MemberConverter().convert(ctx, str(updated_case.case_target_id))
        await self._handle_case_response(ctx, updated_case, "updated", updated_case.case_reason, target)

    async def _handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
    ) -> None:
        """
        Handle the response for a case.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        case : Case | None
            The case to handle the response for.
        action : str
            The action being performed on the case.
        reason : str
            The reason for the case.
        target : discord.Member | discord.User
            The target of the case.
        """

        if case is not None:
            moderator = await commands.MemberConverter().convert(ctx, str(case.case_moderator_id))

            fields = self._create_case_fields(moderator, target, reason)

            embed = await self.create_embed(
                ctx,
                title=f"Case #{case.case_number} ({case.case_type}) {action}",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"]
                if case.case_status is True
                else CONST.EMBED_ICONS["INACTIVE_CASE"],
            )
            embed.set_thumbnail(url=target.avatar)
        else:
            embed = discord.Embed(
                title=f"Case {action}",
                description="Failed to find case.",
                color=CONST.EMBED_COLORS["ERROR"],
            )

        await ctx.reply(embed=embed, delete_after=10, ephemeral=True)

    async def _handle_case_list_response(
        self,
        ctx: commands.Context[commands.Bot],
        cases: list[Case],
        total_cases: int,
    ) -> None:
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        if not cases:
            embed = discord.Embed(
                title="Cases",
                description="No cases found.",
                color=CONST.EMBED_COLORS["ERROR"],
            )
            await ctx.reply(embed=embed, delete_after=10, ephemeral=True)
            return

        cases_per_page = 10
        for i in range(0, len(cases), cases_per_page):
            embed = self._create_case_list_embed(ctx, cases[i : i + cases_per_page], total_cases)
            menu.add_page(embed)

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        menu.add_button(ViewButton.end_session())

        await menu.start()

    def _create_case_fields(
        self,
        moderator: discord.Member,
        target: discord.Member | discord.User,
        reason: str,
    ) -> list[tuple[str, str, bool]]:
        return [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

    def _create_case_list_embed(
        self,
        ctx: commands.Context[commands.Bot],
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

    #     emojis are represented like <:name:id> with an a in front for animated(<a:name:id>)
    # use \:emoji: to get this format
    # for example\:python: sends <:python3:​232720527448342530>
    def _format_emoji(self, emoji: discord.Emoji) -> str:
        return f"<:{emoji.name}:{emoji.id}>"

    def _add_case_to_embed(
        self,
        embed: discord.Embed,
        case: Case,
    ) -> None:
        case_status_emoji = (
            self.bot.get_emoji(emojis["active_case_emoji"])
            if case.case_status
            else self.bot.get_emoji(emojis["inactive_case_emoji"])
        )

        case_status = ""
        if case_status_emoji:
            case_status = self._format_emoji(case_status_emoji)

        if case.case_type in [CaseType.BAN, CaseType.UNBAN]:
            case_type_emoji = self.bot.get_emoji(emojis["ban"])
        elif case.case_type == CaseType.KICK:
            case_type_emoji = self.bot.get_emoji(emojis["kick"])
        elif case.case_type in [CaseType.TIMEOUT, CaseType.UNTIMEOUT]:
            case_type_emoji = self.bot.get_emoji(emojis["timeout"])
        elif case.case_type == CaseType.WARN:
            case_type_emoji = self.bot.get_emoji(emojis["warn"])
        elif case.case_type in [CaseType.JAIL, CaseType.UNJAIL]:
            case_type_emoji = self.bot.get_emoji(emojis["jail"])
        else:
            case_type_emoji = None

        if case_type_emoji:
            case_type = self._format_emoji(case_type_emoji)

        if case.case_type in [
            CaseType.BAN,
            CaseType.KICK,
            CaseType.TIMEOUT,
            CaseType.WARN,
            CaseType.JAIL,
        ]:
            case_action_emoji = self.bot.get_emoji(emojis["added"])

        elif case.case_type in [CaseType.UNBAN, CaseType.UNTIMEOUT, CaseType.UNJAIL]:
            case_action_emoji = self.bot.get_emoji(emojis["removed"])

        else:
            case_action_emoji = None

        if case_action_emoji:
            case_action = self._format_emoji(case_action_emoji)
        if case_type_emoji:
            case_type = self._format_emoji(case_type_emoji)

        case_type = self._format_emoji(case_type_emoji) if case_type_emoji else ""
        case_action = ""
        if case_action_emoji:
            case_action = self._format_emoji(case_action_emoji)

        case_type_and_action = f"{case_action} {case_type}" if case_action_emoji and case_type_emoji else "Unknown"

        case_date = discord.utils.format_dt(case.case_created_at, "R") if case.case_created_at else "Unknown"
        case_number = f"{case.case_number:04d}"

        if not embed.description:
            embed.description = "**Case**\u2002\u2002\u2002\u2002\u2002**Type**\u2002\u2002\u2002**Date**\n"
        embed.description += (
            f"{case_status} `{case_number}`\u2002\u2002 {case_type_and_action} \u2002\u2002*{case_date}*\n"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Cases(bot))
