import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class ArchWiki(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.base_url = "https://wiki.archlinux.org/api.php"

    def query_archwiki(self, search_term: str) -> tuple[str, str]:
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
            response = client.get(self.base_url, params=params)
            logger.info(f"GET request to {self.base_url} with params {params}")

        logger.info(f"URL: {response.url}")

        # example response: ["pacman",["Pacman"],[""],["https://wiki.archlinux.org/title/Pacman"]]

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return (data[1][0], data[3][0]) if data[1] else ("error", "error")
        return "error", "error"

    @app_commands.command(name="archwiki", description="Search the Arch Wiki.")
    @app_commands.describe(query="The search query.")
    async def archwiki(self, interaction: discord.Interaction, query: str) -> None:
        """
        Search the Arch Wiki for a given query and return the title and URL of the first search result.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        query : str
            The search query.
        """

        title: tuple[str, str] = self.query_archwiki(query)

        if title[0] == "error":
            embed = EmbedCreator.create_error_embed(
                title="Error", description="No search results found.", interaction=interaction
            )

        else:
            embed = EmbedCreator.create_info_embed(
                title=title[0],
                description=title[1],
                interaction=interaction,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ArchWiki(bot))
