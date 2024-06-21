import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.services import xkcd
from tux.utils.embeds import EmbedCreator


class Xkcd(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.client = xkcd.Client()

    xkcd = app_commands.Group(name="xkcd", description="xkcd-related commands")

    @xkcd.command(name="latest", description="Get the latest xkcd comic")
    async def latest(self, interaction: discord.Interaction) -> None:
        embed, ephemeral = await self.get_comic_and_embed(latest=True)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @xkcd.command(name="random", description="Get a random xkcd comic")
    async def random(self, interaction: discord.Interaction) -> None:
        embed, ephemeral = await self.get_comic_and_embed()
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @xkcd.command(name="specific", description="Search for a specific xkcd comic")
    async def specific(self, interaction: discord.Interaction, comic_id: int) -> None:
        embed, ephemeral = await self.get_comic_and_embed(number=comic_id)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    async def get_comic_and_embed(
        self, latest: bool = False, number: int | None = None
    ) -> tuple[discord.Embed, bool]:
        """
        Get the xkcd comic and create an embed.
        """
        try:
            if latest:
                comic = self.client.get_latest_comic(raw_comic_image=True)
            elif number:
                comic = self.client.get_comic(number, raw_comic_image=True)
            else:
                comic = self.client.get_random_comic(raw_comic_image=True)

            description = f"[Explainxkcd]({comic.explanation_url}) | [Webpage]({comic.comic_url})"

            embed = EmbedCreator.create_success_embed(
                title=f"xkcd {comic.id} - {comic.title}",
                description=description,
            )

            embed.set_image(url=comic.image_url)
            ephemeral = False

        except xkcd.HttpError:
            logger.error("HTTP error occurred while fetching xkcd comic")
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="I couldn't find the xkcd comic. Please try again later.",
            )
            ephemeral = True
            return embed, ephemeral

        except Exception as e:
            logger.error(f"Error getting xkcd comic: {e}")
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="An error occurred while fetching the xkcd comic",
            )
            ephemeral = True
            return embed, ephemeral

        else:
            return embed, ephemeral


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Xkcd(bot))
