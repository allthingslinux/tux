"""
Wikipedia and wiki search functionality.

This module provides commands to search and retrieve information from
Arch Linux Wiki and ATL Wiki, with formatted Discord embeds for results.
"""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.http_client import http_client
from tux.services.sentry import capture_api_error
from tux.ui.embeds import EmbedCreator


class Wiki(BaseCog):
    """Discord cog for wiki search functionality."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Wiki cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self.arch_wiki_api_url = "https://wiki.archlinux.org/api.php"
        self.atl_wiki_api_url = "https://atl.wiki/api.php"

    def create_embed(
        self,
        title: tuple[str, str],
        ctx: commands.Context[Tux],
    ) -> discord.Embed:
        """
        Create a Discord embed message based on the search result.

        Parameters
        ----------
        title : tuple[str, str]
            A tuple containing the title and description of the search result.
            If the first element is "error", it indicates no search results were found.
        ctx : commands.Context[Tux]
            The context object for the command.

        Returns
        -------
        discord.Embed
            The created embed message.
        """
        if title[0] == "error":
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description="No search results found.",
            )
        else:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.INFO,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title=title[0],
                description=title[1],
            )
        return embed

    async def query_wiki(self, base_url: str, search_term: str) -> tuple[str, str]:
        """
        Query a wiki API for a search term and return the title and URL of the first search result.

        Parameters
        ----------
        base_url : str
            The base URL of the wiki API.
        search_term : str
            The search term to query the wiki API with.

        Returns
        -------
        tuple[str, str]
            The title and URL of the first search result.
        """
        search_term = search_term.capitalize()
        params: dict[str, str] = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_term,
        }

        try:
            # Send a GET request to the wiki API
            response = await http_client.get(base_url, params=params)
            logger.info(f"GET request to {base_url} with params {params!r}")
            response.raise_for_status()

            # Parse JSON response
            data = response.json()
            logger.info(f"Wiki API response: {data!r}")

            if data.get("query") and data["query"].get("search"):
                search_results = data["query"]["search"]
                if search_results:
                    title = search_results[0]["title"]
                    url_title = title.replace(" ", "_")
                    if "atl.wiki" in base_url:
                        url = f"https://atl.wiki/{url_title}"
                    else:
                        url = f"https://wiki.archlinux.org/title/{url_title}"
                    return title, url
        except Exception as e:
            logger.error(f"Wiki API request failed: {e}")

            capture_api_error(e, endpoint="wiki_api")
            return "error", "error"

        return "error", "error"

    @commands.hybrid_group(
        name="wiki",
        aliases=["wk"],
    )
    async def wiki(self, ctx: commands.Context[Tux]) -> None:
        """
        Wiki related commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("wiki")

    @wiki.command(
        name="arch",
    )
    async def arch_wiki(self, ctx: commands.Context[Tux], query: str) -> None:
        """
        Search the Arch Linux Wiki.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        query : str
            The search query.
        """
        title: tuple[str, str] = await self.query_wiki(self.arch_wiki_api_url, query)

        embed = self.create_embed(title, ctx)

        await ctx.send(embed=embed)

    @wiki.command(
        name="atl",
    )
    async def atl_wiki(self, ctx: commands.Context[Tux], query: str) -> None:
        """
        Search the All Things Linux Wiki.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        query : str
            The search query.
        """
        title: tuple[str, str] = await self.query_wiki(self.atl_wiki_api_url, query)

        embed = self.create_embed(title, ctx)

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the Wiki cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Wiki(bot))
