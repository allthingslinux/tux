"""
Wikipedia and wiki search functionality.

This module provides commands to search and retrieve information from
Arch Linux Wiki and ATL Wiki, with formatted Discord embeds for results.
"""

import re

import discord
import httpx
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
        Query a wiki API for a search term and return the title and URL of the first English result.

        Parameters
        ----------
        base_url : str
            The base URL of the wiki API.
        search_term : str
            The search term to query the wiki API with.

        Returns
        -------
        tuple[str, str]
            The title and URL of the first English search result.
            Returns ("error", "error") if no English results are found.
        """
        search_term = search_term.capitalize()
        params: dict[str, str | int] = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_term,
            "srlimit": 50,  # Get more results to find English ones
        }

        # Pattern to match language codes in parentheses at the start of title or after a slash
        # ArchWiki uses format like "Page Name (Language)/Subpage" for translated pages
        # Matches patterns like "(Italiano)", "(Español)", "(Français)" etc.
        # Only matches if it appears early in the title (before first slash or in first 50 chars)
        language_pattern = re.compile(r"^[^/]*\([^)]+\)")

        try:
            # Send a GET request to the wiki API
            response = await http_client.get(base_url, params=params)
            logger.debug(f"GET request to {base_url} with params {params!r}")
            response.raise_for_status()

            # Parse JSON response
            data = response.json()
            logger.debug(f"Wiki API response received for {base_url}")

            if data.get("query") and data["query"].get("search"):
                search_results = data["query"]["search"]
                if search_results:
                    # Filter for English results (exclude titles with language codes in parentheses)
                    for result in search_results:
                        title = result["title"]
                        # Check if title contains a language code pattern
                        # English pages typically don't have language codes in parentheses
                        if not language_pattern.search(title):
                            url_title = title.replace(" ", "_")
                            if "atl.wiki" in base_url:
                                url = f"https://atl.wiki/{url_title}"
                            else:
                                url = f"https://wiki.archlinux.org/title/{url_title}"
                            return title, url
        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors (403, 404, etc.)
            if e.response.status_code == 403:
                logger.warning(
                    f"Wiki API returned 403 Forbidden for {base_url}. "
                    "The API may be rate-limiting or blocking requests.",
                )
            else:
                logger.error(f"Wiki API returned {e.response.status_code}: {e}")
            capture_api_error(e, endpoint="wiki_api")
            return "error", "error"
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
        # Defer early to acknowledge interaction before async work
        await ctx.defer(ephemeral=True)

        title: tuple[str, str] = await self.query_wiki(self.arch_wiki_api_url, query)

        embed = self.create_embed(title, ctx)

        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
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
        # Defer early to acknowledge interaction before async work
        await ctx.defer(ephemeral=True)

        title: tuple[str, str] = await self.query_wiki(self.atl_wiki_api_url, query)

        embed = self.create_embed(title, ctx)

        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the Wiki cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Wiki(bot))
