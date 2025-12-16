"""
List snippets commands.

This module provides functionality for listing and browsing
all available code snippets in Discord guilds.
"""

from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from sqlalchemy import desc

from tux.core.bot import Tux
from tux.database.models import Snippet
from tux.shared.constants import SNIPPET_PAGINATION_LIMIT

from . import SnippetsBaseCog


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

        # Fetch snippets with database-level ordering and optional search
        if search_query:
            filtered_snippets = await self.db.snippet.search_snippets(
                ctx.guild.id,
                search_query,
            )
            # Sort search results by usage count (most used first)
            filtered_snippets.sort(key=lambda s: s.uses, reverse=True)
        else:
            # Fetch all snippets ordered by usage count from database
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

        # Set up pagination menu
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed, show_page_director=False)

        # Add pages based on filtered snippets
        total_snippets = len(filtered_snippets)

        for i in range(0, total_snippets, SNIPPET_PAGINATION_LIMIT):
            page_snippets = filtered_snippets[i : i + SNIPPET_PAGINATION_LIMIT]

            embed = self._create_snippets_list_embed(
                ctx,
                page_snippets,
                total_snippets,
                search_query,
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
