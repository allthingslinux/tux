from bot import Tux
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from utils.constants import CONST
from utils.functions import generate_usage

from prisma.models import Snippet

from . import SnippetsBaseCog


class ListSnippets(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.list_snippets.usage = generate_usage(self.list_snippets)

    @commands.command(
        name="snippets",
        aliases=["ls"],
    )
    @commands.guild_only()
    async def list_snippets(self, ctx: commands.Context[Tux], *, search_query: str | None = None) -> None:
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

        # Fetch all snippets for the guild
        # Sorting by creation date first might be slightly inefficient if we immediately resort by uses.
        # Consider fetching sorted by uses if the DB supports it efficiently, or fetching unsorted.

        all_snippets: list[Snippet] = await self.db.snippet.get_all_snippets_by_guild_id(ctx.guild.id)

        # Sort by usage count (most used first)
        all_snippets.sort(key=lambda s: s.uses, reverse=True)

        # Apply search filter if provided
        filtered_snippets = all_snippets

        if search_query:
            query = search_query.lower()
            filtered_snippets = [
                snippet
                for snippet in all_snippets
                if query in (snippet.snippet_name or "").lower() or query in (snippet.snippet_content or "").lower()
            ]

        if not filtered_snippets:
            await self.send_snippet_error(
                ctx,
                description="No snippets found matching your query." if search_query else "No snippets found.",
            )
            return

        # Set up pagination menu
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed, show_page_director=False)

        # Add pages based on filtered snippets
        total_snippets = len(filtered_snippets)

        for i in range(0, total_snippets, CONST.SNIPPET_PAGINATION_LIMIT):
            page_snippets = filtered_snippets[i : i + CONST.SNIPPET_PAGINATION_LIMIT]

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
