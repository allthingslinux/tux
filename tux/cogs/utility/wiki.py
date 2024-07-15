import httpx
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Wiki(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.arch_wiki_base_url = "https://wiki.archlinux.org/api.php"
        self.atl_wiki_base_url = "https://atl.wiki/api.php"

    def query_arch_wiki(self, search_term: str) -> tuple[str, str]:
        """
        Query the ArchWiki API for a search term and return the title and URL of the first search result.

        Parameters
        ----------
        search_term : str
            The search term to query the ArchWiki API with.

        Returns
        -------
        tuple[str, str]
            The title and URL of the first search result.
        """

        params: dict[str, str] = {
            "action": "opensearch",
            "format": "json",
            "limit": "1",
            "search": search_term,
        }

        # Send a GET request to the ArchWiki API
        with httpx.Client() as client:
            response = client.get(self.arch_wiki_base_url, params=params)
            logger.info(f"GET request to {self.arch_wiki_base_url} with params {params}")

        # example response: ["pacman",["Pacman"],[""],["https://wiki.archlinux.org/title/Pacman"]]

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return (data[1][0], data[3][0]) if data[1] else ("error", "error")
        return "error", "error"

    def query_atl_wiki(self, search_term: str) -> tuple[str, str]:
        """
        Query the atl.wiki API for a search term and return the title and URL of the first search result.

        Parameters
        ----------
        search_term : str
            The search term to query the atl.wiki API with.

        Returns
        -------
        tuple[str, str]
            The title and URL of the first search result.
        """

        params: dict[str, str] = {
            "action": "opensearch",
            "format": "json",
            "limit": "1",
            "search": search_term,
        }

        # Send a GET request to the ATL Wiki API
        with httpx.Client() as client:
            response = client.get(self.atl_wiki_base_url, params=params)
            logger.info(f"GET request to {self.atl_wiki_base_url} with params {params}")

        # example response: ["pacman",["Pacman"],[""],["https://atl.wiki/title/Pacman"]]

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return (data[1][0], data[3][0]) if data[1] else ("error", "error")
        return "error", "error"

    @commands.hybrid_group(
        name="wiki",
        usage="$wiki [arch|atl]",
    )
    async def wiki(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Wiki related commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help("wiki")

    @wiki.command(
        name="arch",
        usage="$wiki arch [query]",
    )
    async def arch_wiki(self, ctx: commands.Context[commands.Bot], query: str) -> None:
        """
        Search the Arch Linux Wiki

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        query : str
            The search query.
        """

        title: tuple[str, str] = self.query_arch_wiki(query)

        if title[0] == "error":
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="No search results found.",
                ctx=ctx,
            )

        else:
            embed = EmbedCreator.create_info_embed(title=title[0], description=title[1], ctx=ctx)

        await ctx.reply(embed=embed)

    @wiki.command(
        name="atl",
        usage="$wiki atl [query]",
    )
    async def atl_wiki(self, ctx: commands.Context[commands.Bot], query: str) -> None:
        """
        Search the All Things Linux Wiki

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        query : str
            The search query.
        """

        title: tuple[str, str] = self.query_atl_wiki(query)

        if title[0] == "error":
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="No search results found.",
                ctx=ctx,
            )

        else:
            embed = EmbedCreator.create_info_embed(title=title[0], description=title[1], ctx=ctx)

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Wiki(bot))
