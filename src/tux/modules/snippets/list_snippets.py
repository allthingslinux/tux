"""
List snippets commands.

This module provides functionality for listing and browsing
all available code snippets in Discord guilds.
"""

import discord
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from sqlalchemy import desc

from tux.core.bot import Tux
from tux.core.converters import FlexibleUserConverter
from tux.database.models import Snippet
from tux.shared.constants import SNIPPET_PAGINATION_LIMIT

from . import SnippetsBaseCog

_MEMBER_PARAM = commands.param(default=None, converter=FlexibleUserConverter())


class ListSnippets(SnippetsBaseCog):
    """Discord cog for listing snippets."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the list snippets cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.command(
        name="snippets",
        aliases=["ls"],
    )
    @commands.guild_only()
    async def list_snippets(
        self,
        ctx: commands.Context[Tux],
        *,
        search_query: str | None = None,
    ) -> None:
        """List snippets, optionally filtering by a search query.

        Displays snippets in a paginated embed, sorted by usage count (descending).
        The search query filters by snippet name or content (case-insensitive).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        search_query : str | None, optional
            The query to filter snippets by name or content.
        """
        assert ctx.guild

        if search_query:
            filtered_snippets = await self.db.snippet.search_snippets(
                ctx.guild.id,
                search_query,
            )
            filtered_snippets.sort(key=lambda s: s.uses, reverse=True)
        else:
            filtered_snippets = await self.db.snippet.get_all_snippets_by_guild_id(
                ctx.guild.id,
                order_by=desc(Snippet.__table__.c.uses),  # type: ignore[attr-defined]
            )

        if not filtered_snippets:
            await self.send_snippet_error(
                ctx,
                description="No snippets found matching your query."
                if search_query
                else "No snippets found.",
            )
            return

        await self._send_snippets_menu(
            ctx,
            filtered_snippets,
            search_query=search_query,
        )

    @commands.command(
        name="lsf",
        aliases=["listsnippetsfrom", "lsb"],
    )
    @commands.guild_only()
    async def list_snippets_from(
        self,
        ctx: commands.Context[Tux],
        member: discord.User | None = _MEMBER_PARAM,
        *,
        search_query: str | None = None,
    ) -> None:
        """List snippets from a specific member, with an optional search query.

        Displays snippets in a paginated embed, sorted by usage count (descending).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        member : discord.User | None
            The member whose snippets to list.
        search_query : str | None, optional
            The query to further filter snippets by name or content.
        """
        assert ctx.guild

        if member is None:
            await self.send_snippet_error(
                ctx,
                description="Please provide a member to list snippets from.",
            )
            return

        filtered_snippets = await self.db.snippet.get_snippets_by_creator(
            member.id,
            ctx.guild.id,
        )
        filtered_snippets.sort(key=lambda s: s.uses, reverse=True)

        if search_query:
            sq = search_query.lower()
            filtered_snippets = [
                s
                for s in filtered_snippets
                if sq in s.snippet_name.lower() or sq in s.snippet_content.lower()
            ]

        if not filtered_snippets:
            await self.send_snippet_error(
                ctx,
                description=f"No snippets found for {member.display_name}."
                if not search_query
                else f"No snippets found for {member.display_name} matching your query.",
            )
            return

        await self._send_snippets_menu(
            ctx,
            filtered_snippets,
            search_query=search_query,
            member=member,
        )

    async def _send_snippets_menu(
        self,
        ctx: commands.Context[Tux],
        snippets: list[Snippet],
        search_query: str | None = None,
        member: discord.User | None = None,
    ) -> None:
        """Build and start a paginated ViewMenu for a list of snippets."""
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed, show_page_director=False)

        total_snippets = len(snippets)

        for i in range(0, total_snippets, SNIPPET_PAGINATION_LIMIT):
            page_snippets = snippets[i : i + SNIPPET_PAGINATION_LIMIT]
            embed = self._create_snippets_list_embed(
                ctx,
                page_snippets,
                total_snippets,
                search_query,
                member,
            )
            menu.add_page(embed)

        menu.add_buttons(
            [
                ViewButton.go_to_first_page(),
                ViewButton.back(),
                ViewButton.next(),
                ViewButton.go_to_last_page(),
                ViewButton.end_session(),
            ],
        )

        await menu.start()


async def setup(bot: Tux) -> None:
    """Load the ListSnippets cog."""
    await bot.add_cog(ListSnippets(bot))
