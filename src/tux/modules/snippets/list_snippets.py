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
        member: discord.User | None = _MEMBER_PARAM,
        *,
        search_query: str | None = None,
    ) -> None:
        """List snippets, optionally filtering by member or search query.

        Displays snippets in a paginated embed, sorted by usage count (descending).
        Optionally filter by a member's snippets or a search query.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        member : discord.User | None, optional
            The member whose snippets to list.
        search_query : str | None, optional
            The query to filter snippets by name or content.
        """
        assert ctx.guild

        if member is not None:
            filtered_snippets = await self.db.snippet.get_snippets_by_creator(
                member.id,
                ctx.guild.id,
            )
            filtered_snippets.sort(key=lambda s: s.uses, reverse=True)
        elif search_query:
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
                description=f"No snippets found for {member.display_name}."
                if member
                else "No snippets found matching your query."
                if search_query
                else "No snippets found.",
            )
            return

        # Set up pagination menu
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed, show_page_director=False)

        total_snippets = len(filtered_snippets)

        for i in range(0, total_snippets, SNIPPET_PAGINATION_LIMIT):
            page_snippets = filtered_snippets[i : i + SNIPPET_PAGINATION_LIMIT]

            embed = self._create_snippets_list_embed(
                ctx,
                page_snippets,
                total_snippets,
                search_query,
                member,
            )

            menu.add_page(embed)

        menu_buttons = [
            ViewButton.go_to_first_page(),
            ViewButton.back(),
            ViewButton.next(),
            ViewButton.go_to_last_page(),
            ViewButton.end_session(),
        ]

        menu.add_buttons(menu_buttons)

        await menu.start()


async def setup(bot: Tux) -> None:
    """Load the ListSnippets cog."""
    await bot.add_cog(ListSnippets(bot))
