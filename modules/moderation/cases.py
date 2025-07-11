from typing import Any, Protocol

import discord
from bot import Tux
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu
from ui.embeds import EmbedCreator, EmbedType
from utils import checks
from utils.constants import CONST
from utils.flags import CaseModifyFlags, CasesViewFlags
from utils.functions import generate_usage

from prisma.enums import CaseType
from prisma.models import Case
from prisma.types import CaseWhereInput

from . import ModerationCogBase

# Maps case types to their corresponding emoji keys
CASE_TYPE_EMOJI_MAP = {
    CaseType.BAN: "ban",
    CaseType.UNBAN: "ban",
    CaseType.TEMPBAN: "tempban",
    CaseType.KICK: "kick",
    CaseType.TIMEOUT: "timeout",
    CaseType.UNTIMEOUT: "timeout",
    CaseType.WARN: "warn",
    CaseType.JAIL: "jail",
    CaseType.UNJAIL: "jail",
    CaseType.SNIPPETBAN: "snippetban",
    CaseType.SNIPPETUNBAN: "snippetunban",
}

# Maps case types to their action (added/removed)
CASE_ACTION_MAP = {
    CaseType.BAN: "added",
    CaseType.KICK: "added",
    CaseType.TEMPBAN: "added",
    CaseType.TIMEOUT: "added",
    CaseType.WARN: "added",
    CaseType.JAIL: "added",
    CaseType.SNIPPETBAN: "added",
    CaseType.UNBAN: "removed",
    CaseType.UNTIMEOUT: "removed",
    CaseType.UNJAIL: "removed",
    CaseType.SNIPPETUNBAN: "removed",
}


# Define a protocol for user-like objects
class UserLike(Protocol):
    id: int
    name: str
    avatar: Any

    def __str__(self) -> str: ...


# Mock user object for when a user cannot be found
class MockUser:
    """A mock user object for cases where we can't find the real user."""

    def __init__(self, user_id: int) -> None:
        self.id = user_id
        self.name = "Unknown User"
        self.discriminator = "0000"
        self.avatar = None

    def __str__(self) -> str:
        return f"{self.name}#{self.discriminator}"


class Cases(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.cases.usage = generate_usage(self.cases)
        self.cases_view.usage = generate_usage(self.cases_view, CasesViewFlags)
        self.cases_modify.usage = generate_usage(
            self.cases_modify,
            CaseModifyFlags,
        )

    @commands.hybrid_group(
        name="cases",
        aliases=["case", "c"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases(self, ctx: commands.Context[Tux], case_number: str | None = None) -> None:
        """
        Manage moderation cases in the server.

        Parameters
        ----------
        case_number : str | None
            The case number to view.
        """

        if case_number is not None:
            await ctx.invoke(self.cases_view, number=case_number, flags=CasesViewFlags())

        elif ctx.subcommand_passed is None:
            await ctx.invoke(self.cases_view, number=None, flags=CasesViewFlags())

    @cases.command(
        name="view",
        aliases=["v", "ls", "list"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def cases_view(
        self,
        ctx: commands.Context[Tux],
        number: str | None = None,
        *,
        flags: CasesViewFlags,
    ) -> None:
        """
        View moderation cases in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        number : Optional[str]
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
        number: str,
        *,
        flags: CaseModifyFlags,
    ) -> None:
        """
        Modify a moderation case in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        number : str
            The case number to modify.
        flags : CaseModifyFlags
            The flags for the command. (status, reason)
        """
        assert ctx.guild

        try:
            case_number = int(number)
        except ValueError:
            await ctx.send("Case number must be a valid integer.", ephemeral=True)
            return

        case = await self.db.case.get_case_by_number(ctx.guild.id, case_number)
        if not case:
            await ctx.send("Case not found.", ephemeral=True)
            return

        # Validate flags
        if flags.status is None and not flags.reason:
            await ctx.send("You must provide either a new status or reason.", ephemeral=True)
            return

        # Check if status is valid
        if flags.status is not None:
            try:
                flags.status = bool(flags.status)
                if flags.status == case.case_status:
                    await ctx.send("Status is already set to that value.", ephemeral=True)
                    return

            except ValueError:
                await ctx.send("Status must be a boolean value (true/false).", ephemeral=True)
                return

        # Check if reason is the same
        if flags.reason is not None and flags.reason == case.case_reason:
            await ctx.send("Reason is already set to that value.", ephemeral=True)
            return

        # If we get here, we have valid changes to make
        await self._update_case(ctx, case, flags)

    async def _view_single_case(
        self,
        ctx: commands.Context[Tux],
        number: str,
    ) -> None:
        """
        View a single case by its number.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        number : str
            The number of the case to view.
        """
        assert ctx.guild

        try:
            case_number = int(number)
        except ValueError:
            await self.send_error_response(ctx, "Case number must be a valid integer.")
            return

        case = await self.db.case.get_case_by_number(ctx.guild.id, case_number)
        if not case:
            await self.send_error_response(ctx, "Case not found.")
            return

        user = await self._resolve_user(case.case_user_id)
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

        if not cases:
            await ctx.send("No cases found.", ephemeral=True)
            return

        total_cases = await self.db.case.get_all_cases(ctx.guild.id)

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
        assert case.case_number is not None

        updated_case = await self.db.case.update_case(
            ctx.guild.id,
            case.case_number,
            case_reason=flags.reason if flags.reason is not None else case.case_reason,
            case_status=flags.status if flags.status is not None else case.case_status,
        )

        if not updated_case:
            await self.send_error_response(ctx, "Failed to update case.")
            return

        user = await self._resolve_user(case.case_user_id)
        await self._handle_case_response(ctx, updated_case, "updated", updated_case.case_reason, user)

    async def _resolve_user(self, user_id: int) -> discord.User | MockUser:
        """
        Resolve a user ID to a User object or MockUser if not found.

        Parameters
        ----------
        user_id : int
            The ID of the user to resolve.

        Returns
        -------
        Union[discord.User, MockUser]
            The resolved user or a mock user if not found.
        """
        if user := self.bot.get_user(user_id):
            return user

        # If not in cache, try fetching
        try:
            return await self.bot.fetch_user(user_id)

        except discord.NotFound:
            logger.warning(f"Could not find user with ID {user_id}")
            return MockUser(user_id)
        except Exception as e:
            logger.exception(f"Error resolving user with ID {user_id}: {e}")
            return MockUser(user_id)

    async def _resolve_moderator(self, moderator_id: int) -> discord.User | MockUser:
        """
        Resolve a moderator ID to a User object or MockUser if not found.
        We use a separate function to potentially add admin-specific
        resolution in the future.

        Parameters
        ----------
        moderator_id : int
            The ID of the moderator to resolve.

        Returns
        -------
        Union[discord.User, MockUser]
            The resolved moderator or a mock user if not found.
        """
        return await self._resolve_user(moderator_id)

    async def _handle_case_response(
        self,
        ctx: commands.Context[Tux],
        case: Case | None,
        action: str,
        reason: str,
        user: discord.User | MockUser,
    ) -> None:
        """
        Handle the response for a case.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case : Optional[Case]
            The case to handle the response for.
        action : str
            The action being performed on the case.
        reason : str
            The reason for the case.
        user : Union[discord.User, MockUser]
            The target of the case.
        """
        if not case:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title=f"Case {action}",
                description="Failed to find case.",
            )

            await ctx.send(embed=embed, ephemeral=True)
            return

        moderator = await self._resolve_moderator(case.case_moderator_id)
        fields = self._create_case_fields(moderator, user, reason)

        embed = self.create_embed(
            ctx,
            title=f"Case #{case.case_number} ({case.case_type}) {action}",
            fields=fields,
            color=CONST.EMBED_COLORS["CASE"],
            icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"] if case.case_status else CONST.EMBED_ICONS["INACTIVE_CASE"],
        )

        # Safe avatar access that works with MockUser
        if hasattr(user, "avatar") and user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        await ctx.send(embed=embed, ephemeral=True)

    async def _handle_case_list_response(
        self,
        ctx: commands.Context[Tux],
        cases: list[Case],
        total_cases: int,
    ) -> None:
        """
        Handle the response for a case list.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        cases : list[Case]
            The cases to handle the response for.
        total_cases : int
            The total number of cases.
        """
        if not cases:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title="Cases",
                description="No cases found.",
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        menu = ViewMenu(
            ctx,
            menu_type=ViewMenu.TypeEmbed,
            all_can_click=True,
            delete_on_timeout=True,
        )

        # Paginate cases
        cases_per_page = 10

        for i in range(0, len(cases), cases_per_page):
            embed = self._create_case_list_embed(
                ctx,
                cases[i : i + cases_per_page],
                total_cases,
            )

            menu.add_page(embed)

        menu_buttons = [
            ViewButton(
                style=discord.ButtonStyle.secondary,
                custom_id=ViewButton.ID_GO_TO_FIRST_PAGE,
                emoji="⏮️",
            ),
            ViewButton(
                style=discord.ButtonStyle.secondary,
                custom_id=ViewButton.ID_PREVIOUS_PAGE,
                emoji="⏪",
            ),
            ViewButton(
                style=discord.ButtonStyle.secondary,
                custom_id=ViewButton.ID_NEXT_PAGE,
                emoji="⏩",
            ),
            ViewButton(
                style=discord.ButtonStyle.secondary,
                custom_id=ViewButton.ID_GO_TO_LAST_PAGE,
                emoji="⏭️",
            ),
        ]

        menu.add_buttons(menu_buttons)

        await menu.start()

    @staticmethod
    def _create_case_fields(
        moderator: discord.User | MockUser,
        user: discord.User | MockUser,
        reason: str,
    ) -> list[tuple[str, str, bool]]:
        """
        Create the fields for a case.

        Parameters
        ----------
        moderator : Union[discord.User, MockUser]
            The moderator of the case.
        user : Union[discord.User, MockUser]
            The user of the case.
        reason : str
            The reason for the case.

        Returns
        -------
        list[tuple[str, str, bool]]
            The fields for the case.
        """
        return [
            (
                "Moderator",
                f"**{moderator}**\n`{moderator.id if hasattr(moderator, 'id') else 'Unknown'}`",
                True,
            ),
            ("User", f"**{user}**\n`{user.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

    def _create_case_list_embed(
        self,
        ctx: commands.Context[Tux],
        cases: list[Case],
        total_cases: int,
    ) -> discord.Embed:
        """
        Create the embed for a case list.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        cases : list[Case]
            The cases to create the embed for.
        total_cases : int
            The total number of cases.

        Returns
        -------
        discord.Embed
            The embed for the case list.
        """
        assert ctx.guild
        assert ctx.guild.icon

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=self.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        embed = EmbedCreator.create_embed(
            title=f"Total Cases ({total_cases})",
            description="",
            embed_type=EmbedType.CASE,
            custom_author_text=ctx.guild.name,
            custom_author_icon_url=ctx.guild.icon.url,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

        # Header row for the list
        embed.description = "**Case**\u2003\u2003\u2002**Type**\u2003\u2002**Date**\n"

        # Add each case to the embed
        for case in cases:
            # Get emojis for this case
            status_emoji = self.bot.emoji_manager.get(
                "active_case" if case.case_status else "inactive_case",
            )
            type_emoji = self.bot.emoji_manager.get(
                CASE_TYPE_EMOJI_MAP.get(case.case_type, "tux_error"),
            )
            action_emoji = self.bot.emoji_manager.get(
                CASE_ACTION_MAP.get(case.case_type, "tux_error"),
            )

            # Format the case number
            case_number = f"{case.case_number:04}" if case.case_number is not None else "0000"

            # Format type and action
            case_type_and_action = f"{action_emoji}{type_emoji}"

            # Format date
            case_date = (
                discord.utils.format_dt(
                    case.case_created_at,
                    "R",
                )
                if case.case_created_at
                else f"{self.bot.emoji_manager.get('tux_error')}"
            )

            # Add the line to the embed
            embed.description += f"{status_emoji}`{case_number}`\u2003 {case_type_and_action} \u2003__{case_date}__\n"

        return embed


async def setup(bot: Tux) -> None:
    await bot.add_cog(Cases(bot))
