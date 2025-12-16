"""
Base utilities and classes for snippet management.

This module provides the foundational classes and utilities for managing
code snippets in Discord guilds, including base functionality for snippet
commands and permission checking.
"""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.permission_system import get_permission_system
from tux.database.models import CaseType as DBCaseType
from tux.database.models import Snippet
from tux.shared.config import CONFIG
from tux.ui.embeds import EmbedCreator, EmbedType


class SnippetsBaseCog(BaseCog):
    """Base class for Snippet Cogs, providing shared utilities."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the snippets base cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is currently snippet banned in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is snippet banned, False otherwise.
        """
        return await self.db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,
            inactive_restriction_type=DBCaseType.UNJAIL,
        )

    def _create_snippets_list_embed(
        self,
        ctx: commands.Context[Tux],
        snippets: list[Snippet],
        total_snippets: int,
        search_query: str | None = None,
    ) -> discord.Embed:
        """Create an embed for displaying a paginated list of snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        snippets : list[Snippet]
            The list of snippets for the current page.
        total_snippets : int
            The total number of snippets matching the query.
        search_query : str | None
            The search query used, if any.

        Returns
        -------
        discord.Embed
            The generated embed.
        """
        assert ctx.guild
        assert ctx.guild.icon

        if not snippets:
            return EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description="No snippets found.",
            )

        description = "\n".join(
            f"`{'🔒' if snippet.locked else ' '}{'→' if snippet.alias else ' '}{i + 1}`. {snippet.snippet_name} (`{snippet.uses}` uses)"
            for i, snippet in enumerate(snippets)
        )
        count = len(snippets)
        total_snippets = total_snippets or 0
        embed_title = f"Snippets ({count}/{total_snippets})"

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=ctx.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        return EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=embed_title,
            description=description or "No snippets found.",
            custom_author_text=ctx.guild.name,
            custom_author_icon_url=ctx.guild.icon.url,
            message_timestamp=ctx.message.created_at,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

    async def check_if_user_has_mod_override(self, ctx: commands.Context[Tux]) -> bool:
        """
        Check if the user invoking the command has moderator permissions (rank >= 2).

        Returns
        -------
        bool
            True if user has moderator permissions, False otherwise.
        """
        try:
            if not ctx.guild:
                return False
            permission_system = get_permission_system()
            user_rank = await permission_system.get_user_permission_rank(ctx)
            # Rank 2 = Junior Moderator in default setup
            return user_rank >= 2  # noqa: TRY300
        except Exception as e:
            logger.error(f"Unexpected error in check_if_user_has_mod_override: {e}")
            return False

    async def snippet_check(
        self,
        ctx: commands.Context[Tux],
        snippet_locked: bool = False,
        snippet_user_id: int = 0,
    ) -> tuple[bool, str]:
        """Check if a user is allowed to modify or delete a snippet.

        Checks for moderator override, snippet bans, role restrictions,
        snippet lock status, and snippet ownership.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        snippet_locked : bool, optional
            Whether the snippet is locked. Checked only if True. Defaults to False.
        snippet_user_id : int, optional
            The ID of the snippet's author. Checked only if non-zero. Defaults to 0.

        Returns
        -------
        tuple[bool, str]
            A tuple containing a boolean indicating permission status and a reason string.
        """
        assert ctx.guild

        # Check moderator override first
        if await self.check_if_user_has_mod_override(ctx):
            return True, "Mod override granted."

        # Check snippet ban status
        if await self.is_snippetbanned(ctx.guild.id, ctx.author.id):
            return False, "You are banned from using snippets."

        # Check role restrictions
        if (
            CONFIG.SNIPPETS.LIMIT_TO_ROLE_IDS
            and isinstance(ctx.author, discord.Member)
            and all(
                role.id not in CONFIG.SNIPPETS.ACCESS_ROLE_IDS
                for role in ctx.author.roles
            )
        ):
            roles_str = ", ".join(
                [f"<@&{role_id}>" for role_id in CONFIG.SNIPPETS.ACCESS_ROLE_IDS],
            )
            return (
                False,
                f"You do not have a role that allows you to manage snippets. Accepted roles: {roles_str}",
            )

        # Check lock status
        if snippet_locked:
            return False, "This snippet is locked. You cannot edit or delete it."

        # Check ownership (allow if snippet_user_id is 0 for create operations)
        if snippet_user_id not in (0, ctx.author.id):
            return False, "You can only edit or delete your own snippets."

        return True, "All checks passed."

    async def _get_snippet_or_error(
        self,
        ctx: commands.Context[Tux],
        name: str,
    ) -> Snippet | None:
        """Fetch a snippet by name and guild, sending an error embed if not found.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet to fetch.

        Returns
        -------
        Snippet | None
            The fetched Snippet object, or None if not found.
        """
        assert ctx.guild
        snippet = await self.db.snippet.get_snippet_by_name_and_guild_id(
            name,
            ctx.guild.id,
        )
        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return None
        return snippet

    async def send_snippet_error(
        self,
        ctx: commands.Context[Tux],
        description: str,
    ) -> None:
        """Send a standardized snippet error embed.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        description : str
            The error message description.
        """
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            description=description,
        )
        await ctx.send(embed=embed)

    def _require_snippet_id(self, snippet: Snippet) -> int:
        """Require snippet to have a valid ID.

        Parameters
        ----------
        snippet : Snippet
            The snippet to check.

        Returns
        -------
        int
            The snippet ID.

        Raises
        ------
        ValueError
            If the snippet ID is None.
        """
        if snippet.id is None:
            error_msg = "Snippet ID is invalid"
            raise ValueError(error_msg)
        return snippet.id

    async def _resolve_alias(
        self,
        snippet: Snippet,
        guild_id: int,
    ) -> tuple[Snippet | None, bool]:
        """Resolve a snippet alias to its target snippet.

        Parameters
        ----------
        snippet : Snippet
            The snippet that may be an alias.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        tuple[Snippet | None, bool]
            A tuple containing the resolved snippet (or None if broken) and
            a boolean indicating if the original snippet was an alias.
        """
        if not snippet.alias:
            return snippet, False

        # Fetch the target snippet
        target = await self.db.snippet.get_snippet_by_name_and_guild_id(
            snippet.alias,
            guild_id,
        )

        # Return target if found, None if broken alias
        return (target, True) if target is not None else (None, True)

    def _format_snippet_message(
        self,
        snippet: Snippet,
        is_alias: bool = False,
        alias_name: str | None = None,
    ) -> str:
        """Format a snippet message for display.

        Parameters
        ----------
        snippet : Snippet
            The snippet to format.
        is_alias : bool, optional
            Whether this is an alias snippet. Defaults to False.
        alias_name : str | None, optional
            The name of the alias if this is an alias. Defaults to None.

        Returns
        -------
        str
            The formatted message text.
        """
        if is_alias and alias_name:
            text = f"`{alias_name}.txt -> {snippet.snippet_name}.txt` "
        else:
            text = f"`/snippets/{snippet.snippet_name}.txt` "

        if snippet.locked:
            text += "🔒 "

        text += f"|| {snippet.snippet_content}"

        return text
