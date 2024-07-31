import discord
import httpx
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class Query(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="query",
        aliases=["q"],
        usage="$query [search_term]",
    )
    async def query(self, ctx: commands.Context[commands.Bot], *, search_term: str) -> None:
        """
        Query the DuckDuckGo API for a search term and return a answer.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        search_term : str
            The search term.
        """

        params: dict[str, str] = {
            "q": search_term,
            "format": "json",
        }

        # Send a GET request to the DuckDuckGo API
        with httpx.Client() as client:
            response = client.get("http://api.duckduckgo.com/", params=params)
            logger.info(f"GET request to http://api.duckduckgo.com/ with params {params}")
            logger.info(f"Full API URL: {response.url}")

        # Check if the request was successful
        if response.status_code != 200:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="An error occurred while processing your request. (DDG Provided a non-200 status code)",
                ctx=ctx,
            )
            return

        data = response.json()

        redirect = False
        old_redirect_url = None
        new_search_term = None

        if not data["Abstract"]:
            # Select the first RelatedTopic as an example
            # Note: You might want to implement more sophisticated selection logic here
            if data["RelatedTopics"]:
                # search the first related topic instead and replace the data variable
                # get the search term from the first related topic
                new_search_term = data["RelatedTopics"][0]["FirstURL"].split("/")[-1]
                new_search_term = new_search_term.replace("_", " ")

                redirect = True
                old_redirect_url = data["AbstractURL"]

                # make a new request to the API
                params = {
                    "q": new_search_term,
                    "format": "json",
                }

                with httpx.Client() as client:
                    response = client.get("http://api.duckduckgo.com/", params=params)
                    logger.info(f"GET request to http://api.duckduckgo.com/ with params {params}")

                if response.status_code != 200:
                    embed = EmbedCreator.create_error_embed(
                        title="Error",
                        description="An error occurred while processing your request. (DDG Provided a non-200 status code)",
                        ctx=ctx,
                    )
                    return

                data = response.json()
            else:
                embed = EmbedCreator.create_error_embed(
                    title="Error",
                    description="No results found for the search term.",
                    ctx=ctx,
                )
                await ctx.send(embed=embed, delete_after=30, ephemeral=True)
                return

        embed = discord.Embed(
            title=f'Answer to "{search_term}"',
            description=f"{data['Abstract']}\n\nData from **{data['AbstractURL']}**",
            color=CONST.EMBED_COLORS["INFO"],
            timestamp=EmbedCreator.get_timestamp(ctx, None),
        )

        embed.set_author(
            name=data["Heading"],
            url=data["AbstractURL"],
            icon_url=f"https://duckduckgo.com{data['Image']}" if data["Image"] else CONST.EMBED_ICONS["DEFAULT"],
        )

        embed.set_footer(
            text="Data via DuckDuckGo API.",
            icon_url="https://duckduckgo.com/favicon.png",
        )

        if redirect:
            embed.add_field(
                name="Search Term Changed",
                value=f"Search term changed to: `{new_search_term}` due to no summary text.\n[Old Answer URL]({old_redirect_url})",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Query(bot))
