"""Moderation case management and viewing commands.

This module provides comprehensive case management functionality for Discord
moderation, including viewing, modifying, and managing moderation cases with
interactive menus and detailed information display.
"""

import contextlib
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, Protocol

import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import CaseModifyFlags, CasesViewFlags
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType
from tux.shared.constants import EMBED_COLORS
from tux.ui.embeds import EmbedCreator, EmbedType

from . import ModerationCogBase

# Maps case types to their corresponding emoji keys
CASE_TYPE_EMOJI_MAP: dict[DBCaseType | None, str] = {
    DBCaseType.BAN: "ban",
    DBCaseType.UNBAN: "ban",
    DBCaseType.TEMPBAN: "tempban",
    DBCaseType.KICK: "kick",
    DBCaseType.TIMEOUT: "timeout",
    DBCaseType.UNTIMEOUT: "timeout",
    DBCaseType.WARN: "warn",
    DBCaseType.JAIL: "jail",
    DBCaseType.UNJAIL: "jail",
    DBCaseType.SNIPPETBAN: "snippet",
    DBCaseType.SNIPPETUNBAN: "snippet",
    DBCaseType.POLLBAN: "poll",
    DBCaseType.POLLUNBAN: "poll",
}

# Maps case types to their action (added/removed)
CASE_ACTION_MAP: dict[DBCaseType | None, str] = {
    DBCaseType.BAN: "added",
    DBCaseType.KICK: "added",
    DBCaseType.TEMPBAN: "added",
    DBCaseType.TIMEOUT: "added",
    DBCaseType.WARN: "added",
    DBCaseType.JAIL: "added",
    DBCaseType.UNBAN: "removed",
    DBCaseType.UNTIMEOUT: "removed",
    DBCaseType.UNJAIL: "removed",
    DBCaseType.SNIPPETBAN: "added",
    DBCaseType.POLLBAN: "added",
    DBCaseType.SNIPPETUNBAN: "removed",
    DBCaseType.POLLUNBAN: "removed",
}


# Define a protocol for user-like objects
class UserLike(Protocol):
    """Protocol for objects that behave like Discord users.

    Attributes
    ----------
    id : int
        The user's unique identifier.
    name : str
        The user's display name.
    avatar : Any
        The user's avatar.
    """

    id: int
    name: str
    avatar: Any

    def __str__(self) -> str:
        """Return a string representation of the user.

        Returns
        -------
        str
            String representation of the user.
        """
        ...


# Mock user object for when a user cannot be found
class MockUser:
    """A mock user object for cases where we can't find the real user."""

    def __init__(self, user_id: int) -> None:
        """Initialize a mock user object.

        Parameters
        ----------
        user_id : int
            The ID of the user this mock represents.
        """
        self.id = user_id
        self.name = "Unknown User"
        self.discriminator = "0000"
        self.avatar = None

    def __str__(self) -> str:
        """Return a string representation of the mock user.

        Returns
        -------
        str
            String representation in the format 'Unknown User#0000'.
        """
        return f"{self.name}#{self.discriminator}"


class Cases(ModerationCogBase):
    """Discord cog for moderation case management and viewing.

    This cog provides comprehensive case management functionality including
    viewing, modifying, and managing moderation cases with interactive menus.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Cases cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_group(
        name="cases",
        aliases=["case", "c"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def cases(
        self,
        ctx: commands.Context[Tux],
        argument: str | None = None,
    ) -> None:
        """
        View all moderation cases in the server.

        Use subcommands to view specific cases or filter by criteria.

        Shortcut: `$cases <user>` automatically runs `$cases search -u <user>`.
        """
        if argument is None:
            await self._view_all_cases(ctx)
            return

        # Try to parse as case number first
        # Case numbers are small sequential integers, while Discord user IDs are large (18+ digits)
        # PostgreSQL INTEGER max is 2,147,483,647, but case numbers are typically < 1,000,000
        # If the number is > 10,000,000, it's almost certainly a user ID, not a case number
        max_reasonable_case_number = 10_000_000

        with contextlib.suppress(ValueError):
            case_number = int(argument)
            # Only treat as case number if it's within reasonable range
            if case_number > 0 and case_number <= max_reasonable_case_number:
                await self._view_single_case(ctx, case_number)
                return
            # If it's a large number, fall through to user conversion

        # Try to convert to user/member - if successful, route to search
        try:
            user = await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:
            # Try UserConverter as fallback (for users not in guild)
            try:
                user = await commands.UserConverter().convert(ctx, argument)
            except commands.UserNotFound:
                # If neither case number nor user, show error
                await self._respond(
                    ctx,
                    f"Could not find case number or user '{argument}'. Use a case number (e.g., `123`) or mention a user (e.g., `@user`).",
                )
                return
            else:
                # Route to search with user - create a simple namespace that mimics CasesViewFlags
                flags = SimpleNamespace(user=user, type=None, moderator=None)
                await self._view_cases_with_flags(ctx, flags)
                return
        else:
            # Route to search with user - create a simple namespace that mimics CasesViewFlags
            flags = SimpleNamespace(user=user, type=None, moderator=None)
            await self._view_cases_with_flags(ctx, flags)

    @cases.command(
        name="view",
        aliases=["v", "show", "get", "list"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def cases_view(
        self,
        ctx: commands.Context[Tux],
        case_number: int,
    ) -> None:
        """
        View a specific moderation case by its number.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case_number : int
            The case number to view (e.g., 123).
        """
        # Defer early to acknowledge interaction before async work
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        await self._view_single_case(ctx, case_number)

    @cases.command(
        name="search",
        aliases=["filter", "find"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def cases_search(
        self,
        ctx: commands.Context[Tux],
        *,
        flags: CasesViewFlags,
    ) -> None:
        """
        Search/filter moderation cases by criteria.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        flags : CasesViewFlags
            Filter criteria (--type, --user, --moderator).
        """
        await self._view_cases_with_flags(ctx, flags)

    @cases.command(
        name="modify",
        aliases=["m", "edit", "update"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def cases_modify(
        self,
        ctx: commands.Context[Tux],
        case_number: int,
        *,
        flags: CaseModifyFlags,
    ) -> None:
        """
        Modify a moderation case.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case_number : int
            The case number to modify.
        flags : CaseModifyFlags
            Modification options (--status, --reason).
        """
        assert ctx.guild

        case = await self.db.case.get_case_by_number(case_number, ctx.guild.id)
        if not case:
            if ctx.interaction:
                await ctx.interaction.followup.send("Case not found.", ephemeral=True)
            else:
                await ctx.send("Case not found.")
            return

        # Validate changes
        if not self._has_valid_changes(case, flags):
            if ctx.interaction:
                await ctx.interaction.followup.send(
                    "No valid changes provided.",
                    ephemeral=True,
                )
            else:
                await ctx.send("No valid changes provided.")
            return

        await self._update_case(ctx, case, flags)

    def _has_valid_changes(self, case: Case, flags: CaseModifyFlags) -> bool:
        """
        Check if the modification flags contain valid changes.

        Parameters
        ----------
        case : Case
            The case to check against.
        flags : CaseModifyFlags
            The modification flags.

        Returns
        -------
        bool
            True if valid changes are present, False otherwise.
        """
        # No changes provided at all
        if flags.status is None and not flags.reason:
            return False

        # Check if status is actually changing
        if flags.status is not None and flags.status == case.case_status:
            return False

        # Check if reason is actually changing
        if flags.reason is not None and flags.reason == case.case_reason:
            return False

        # At least one field has a valid change
        return (flags.status is not None and flags.status != case.case_status) or (
            flags.reason is not None and flags.reason != case.case_reason
        )

    async def _view_all_cases(self, ctx: commands.Context[Tux]) -> None:
        """View all cases in the server."""
        assert ctx.guild
        cases = await self.db.case.get_all_cases(ctx.guild.id)

        if not cases:
            if ctx.interaction:
                await ctx.interaction.followup.send("No cases found.", ephemeral=True)
            else:
                await ctx.send("No cases found.")
            return

        await self._handle_case_list_response(ctx, cases, len(cases), {})

    async def _view_single_case(
        self,
        ctx: commands.Context[Tux],
        case_number: int,
    ) -> None:
        """
        View a single case by its number.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case_number : int
            The number of the case to view.
        """
        assert ctx.guild

        case = await self.db.case.get_case_by_number(case_number, ctx.guild.id)
        if not case:
            if ctx.interaction:
                await ctx.interaction.followup.send("Case not found.", ephemeral=True)
            else:
                await ctx.reply("Case not found.", mention_author=False)
            return

        user = await self._resolve_user(case.case_user_id)
        await self._send_case_embed(ctx, case, "viewed", case.case_reason, user)

    async def _view_cases_with_flags(
        self,
        ctx: commands.Context[Tux],
        flags: CasesViewFlags | Any,
    ) -> None:
        """
        View cases with the provided flags.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        flags : CasesViewFlags | Any
            The flags for the command. (type, user, moderator)
            Can be CasesViewFlags or any object with type, user, and moderator attributes.
        """
        assert ctx.guild

        options: dict[str, Any] = {}

        if hasattr(flags, "type") and flags.type:
            options["case_type"] = flags.type
        if hasattr(flags, "user") and flags.user:
            options["user_id"] = flags.user.id
        if hasattr(flags, "moderator") and flags.moderator:
            options["moderator_id"] = flags.moderator.id

        cases = await self.db.case.get_cases_by_options(ctx.guild.id, options)

        if not cases:
            if ctx.interaction:
                await ctx.interaction.followup.send("No cases found.", ephemeral=True)
            else:
                await ctx.send("No cases found.")
            return

        # Use filtered cases count when filters are applied, otherwise get all cases
        if options:
            # Filters are applied, use the filtered count
            total_cases = len(cases)
        else:
            # No filters, get total count of all cases
            all_cases = await self.db.case.get_all_cases(ctx.guild.id)
            total_cases = len(all_cases)

        await self._handle_case_list_response(ctx, cases, total_cases, options)

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

        updated_case = await self.db.case.update_case_by_number(
            ctx.guild.id,
            case.case_number,
            case_reason=flags.reason if flags.reason is not None else case.case_reason,
            case_status=flags.status if flags.status is not None else case.case_status,
        )

        if not updated_case:
            if ctx.interaction:
                await ctx.interaction.followup.send(
                    "Failed to update case.",
                    ephemeral=True,
                )
            else:
                await ctx.reply("Failed to update case.", mention_author=False)
            return

        # Update the mod log embed if it exists
        await self._update_mod_log_embed(ctx, updated_case)

        user = await self._resolve_user(case.case_user_id)
        await self._send_case_embed(
            ctx,
            updated_case,
            "updated",
            updated_case.case_reason,
            user,
        )

    async def _update_mod_log_embed(
        self,
        ctx: commands.Context[Tux],
        case: Case,
    ) -> None:
        """
        Update the mod log embed for a modified case.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case : Case
            The updated case to reflect in the mod log.
        """
        assert ctx.guild

        # Check if this case has a mod log message ID
        if not case.mod_log_message_id:
            logger.debug(
                f"Case #{case.case_number} has no mod log message ID, skipping update",
            )
            return

        mod_message: discord.Message | None = None

        try:
            # Get mod log channel ID from guild config
            _, mod_log_id = await self.bot.db.guild_config.get_log_channel_ids(
                ctx.guild.id,
            )
            if not mod_log_id:
                logger.debug(f"No mod log channel configured for guild {ctx.guild.id}")
                return

            # Get the mod log channel
            mod_channel = ctx.guild.get_channel(mod_log_id)
            if not mod_channel or not isinstance(mod_channel, discord.TextChannel):
                logger.warning(
                    f"Mod log channel {mod_log_id} not found or not a text channel",
                )
                return

            # Try to fetch the mod log message
            try:
                mod_message = await mod_channel.fetch_message(case.mod_log_message_id)
            except discord.NotFound:
                logger.warning(
                    f"Mod log message {case.mod_log_message_id} not found in channel {mod_channel.id}",
                )
                return
            except discord.Forbidden:
                logger.warning(
                    f"Missing permissions to fetch message {case.mod_log_message_id} in mod log channel",
                )
                return

            # Create updated embed for mod log
            user = await self._resolve_user(case.case_user_id)
            moderator = await self._resolve_moderator(case.case_moderator_id)

            # Use correct embed type based on case status
            embed_type = (
                EmbedType.ACTIVE_CASE if case.case_status else EmbedType.INACTIVE_CASE
            )

            embed = EmbedCreator.create_embed(
                embed_type=embed_type,
                description="Case Updated",  # Indicate this is an updated case
                custom_author_text=f"Case #{case.case_number} ({case.case_type.value if case.case_type else 'Unknown'})",
            )

            # Add case-specific fields for mod log
            fields = [
                ("Moderator", f"{moderator.name}\n`{moderator.id}`", True),
                ("Target", f"{user.name}\n`{user.id}`", True),
                ("Reason", f"> {case.case_reason}", False),
            ]

            if case.case_expires_at:
                # Ensure UTC-aware datetime before getting timestamp
                expires_at = (
                    case.case_expires_at.replace(tzinfo=UTC)
                    if case.case_expires_at.tzinfo is None
                    else case.case_expires_at
                )
                fields.append(
                    ("Expires", f"<t:{int(expires_at.timestamp())}:R>", True),
                )

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            # Set embed timestamp to case creation time
            # Ensure UTC-aware datetime (database stores as UTC but returns naive)
            if case.created_at:
                if case.created_at.tzinfo is None:
                    # Naive datetime from database - treat as UTC
                    embed.timestamp = case.created_at.replace(tzinfo=UTC)
                else:
                    embed.timestamp = case.created_at

            # Add footer indicating this was updated
            embed.set_footer(
                text=f"Last updated by {ctx.author} • {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            )

            # Edit the mod log message with updated embed
            await mod_message.edit(embed=embed)
            logger.info(
                f"Updated mod log message {case.mod_log_message_id} for case #{case.case_number}",
            )

        except Exception as e:
            logger.error(
                f"Failed to update mod log embed for case #{case.case_number}: {e}",
            )
            # Don't raise - mod log update failure shouldn't break case modification

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
            # Graceful fallback - don't use exception() level for expected fallback behavior
            logger.warning(f"Error resolving user with ID {user_id}: {e}")
            # Don't send to Sentry - this is expected fallback behavior
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

    async def _send_case_embed(
        self,
        ctx: commands.Context[Tux],
        case: Case | None,
        action: str,
        reason: str,
        user: discord.User | MockUser,
    ) -> None:
        """
        Send an embed response for a case.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        case : Case | None
            The case to send the response for.
        action : str
            The action being performed on the case.
        reason : str
            The reason for the case.
        user : Union[discord.User, MockUser]
            The target of the case.
        """
        if not case:
            embed = discord.Embed(
                title=f"Case {action}",
                description="Failed to find case.",
                color=EMBED_COLORS["ERROR"],
            )
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
            return

        moderator = await self._resolve_moderator(case.case_moderator_id)
        fields = self._create_case_fields(moderator, user, reason)

        # Use correct embed type based on case status
        embed_type = (
            EmbedType.ACTIVE_CASE if case.case_status else EmbedType.INACTIVE_CASE
        )

        # Set embed timestamp to case creation time
        # Ensure UTC-aware datetime (database stores as UTC but returns naive)
        case_timestamp: datetime | None = None
        if case.created_at:
            case_timestamp = (
                case.created_at.replace(tzinfo=UTC)
                if case.created_at.tzinfo is None
                else case.created_at
            )

        embed = EmbedCreator.create_embed(
            embed_type=embed_type,
            custom_author_text=f"Case #{case.case_number} ({case.case_type.value if case.case_type else 'UNKNOWN'}) {action}",
            message_timestamp=case_timestamp,
        )

        # Add fields to embed
        for field in fields:
            name, value, inline = field
            embed.add_field(name=name, value=value, inline=inline)

        # Safe avatar access that works with MockUser
        if hasattr(user, "avatar") and user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

    async def _handle_case_list_response(
        self,
        ctx: commands.Context[Tux],
        cases: list[Case],
        total_cases: int,
        filters: dict[str, Any],
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
        filters : dict[str, Any]
            Dictionary of active filters (user_id, moderator_id, case_type).
        """
        if not cases:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.ERROR,
                title="Cases",
                description="No cases found.",
            )
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
            return

        # Sort cases (highest case id first)
        cases.sort(
            key=lambda x: x.case_number if x.case_number is not None else 0,
            reverse=True,
        )

        # Pass interaction directly to ViewMenu if available (after defer)
        # ViewMenu handles interactions differently than contexts
        menu = ViewMenu(
            ctx.interaction or ctx,
            menu_type=ViewMenu.TypeEmbed,
            all_can_click=True,
        )

        # Paginate cases
        cases_per_page = 10

        for i in range(0, len(cases), cases_per_page):
            embed = self._create_case_list_embed(
                ctx,
                cases[i : i + cases_per_page],
                total_cases,
                filters,
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
        filters: dict[str, Any],
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
        filters : dict[str, Any]
            Dictionary of active filters (user_id, moderator_id, case_type).

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

        # Generate dynamic title based on active filters
        title_parts: list[str] = []
        if filters.get("user_id"):
            user_id = filters["user_id"]
            # Try to get user name from cache or use ID
            user = ctx.guild.get_member(user_id) or ctx.bot.get_user(user_id)
            user_name = user.name if user else f"{user_id}"
            title_parts.append(f"for User: {user_name}")
        if filters.get("moderator_id"):
            moderator_id = filters["moderator_id"]
            # Try to get moderator name from cache or use ID
            moderator = ctx.guild.get_member(moderator_id) or ctx.bot.get_user(
                moderator_id,
            )
            moderator_name = moderator.name if moderator else f"{moderator_id}"
            title_parts.append(f"by Mod: {moderator_name}")
        if filters.get("case_type"):
            case_type = filters["case_type"]
            case_type_value = (
                case_type.value if hasattr(case_type, "value") else str(case_type)
            )
            title_parts.append(f"by Type: {case_type_value}")

        # Build title - join multiple filters with commas for better readability
        if title_parts:
            if len(title_parts) > 1:
                # Multiple filters: "Total Cases for User: X, by Mod: Y, by Type: WARN (2)"
                title = f"Total Cases {', '.join(title_parts)} ({total_cases})"
            else:
                # Single filter: "Total Cases for User: X (2)"
                title = f"Total Cases {title_parts[0]} ({total_cases})"
        else:
            title = f"Total Cases ({total_cases})"

        embed = EmbedCreator.create_embed(
            title=title,
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
            type_emoji_key = CASE_TYPE_EMOJI_MAP.get(case.case_type, "tux_error")
            type_emoji = self.bot.emoji_manager.get(str(type_emoji_key))
            action_emoji_key = CASE_ACTION_MAP.get(case.case_type, "tux_error")
            action_emoji = self.bot.emoji_manager.get(str(action_emoji_key))

            # Format the case number
            case_number = (
                f"{case.case_number:04}" if case.case_number is not None else "0000"
            )

            # Format type and action
            case_type_and_action = f"{action_emoji}{type_emoji}"

            # Format date using created_at timestamp
            # Ensure UTC-aware datetime (database stores as UTC but returns naive)
            if hasattr(case, "created_at") and case.created_at:
                if case.created_at.tzinfo is None:
                    # Naive datetime from database - treat as UTC
                    case_date = discord.utils.format_dt(
                        case.created_at.replace(tzinfo=UTC),
                        "R",
                    )
                else:
                    case_date = discord.utils.format_dt(case.created_at, "R")
            else:
                case_date = f"{self.bot.emoji_manager.get('tux_error')}"

            # Add the line to the embed
            embed.description += f"{status_emoji}`{case_number}`\u2003 {case_type_and_action} \u2003__{case_date}__\n"

        return embed


async def setup(bot: Tux) -> None:
    """Set up the Cases cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Cases(bot))
