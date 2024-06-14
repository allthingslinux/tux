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

    group = app_commands.Group(name="xkcd", description="xkcd-related commands")

    @group.command(name="latest", description="Get the latest xkcd comic")
    async def latest(self, interaction: discord.Interaction) -> None:
        try:
            latest_comic = self.client.get_latest_comic(raw_comic_image=True)
            comic_id = latest_comic.id

            description = f"[Explainxkcd]({latest_comic.explanation_url}) | [Webpage]({latest_comic.comic_url})"

            embed = EmbedCreator.create_success_embed(
                title=f"xkcd {comic_id} - {latest_comic.title}",
                description=description,
                interaction=interaction,
            )

            embed.set_image(url=latest_comic.image_url)

            logger.info(f"{interaction.user} got the latest xkcd comic in {interaction.channel}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error getting the latest xkcd comic: {e}")

            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="An error occurred while fetching the latest xkcd comic",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @group.command(name="random", description="Get a random xkcd comic")
    async def random(self, interaction: discord.Interaction) -> None:
        try:
            random_comic = self.client.get_random_comic(raw_comic_image=True)
            comic_id = random_comic.id

            description = f"[Explainxkcd]({random_comic.explanation_url}) | [Webpage]({random_comic.comic_url})"

            embed = EmbedCreator.create_success_embed(
                title=f"xkcd {comic_id} - {random_comic.title}",
                description=description,
                interaction=interaction,
            )

            embed.set_image(url=random_comic.image_url)

            logger.info(f"{interaction.user} got a random xkcd comic in {interaction.channel}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error getting a random xkcd comic: {e}")

            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="An error occurred while fetching a random xkcd comic",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @group.command(name="specific", description="Search for a specific xkcd comic")
    async def specific(self, interaction: discord.Interaction, comic_id: int) -> None:
        try:
            specific_comic = self.client.get_comic(comic_id, raw_comic_image=True)

            description = f"[Explainxkcd]({specific_comic.explanation_url}) | [Webpage]({specific_comic.comic_url})"

            embed = EmbedCreator.create_success_embed(
                title=f"xkcd {comic_id} - {specific_comic.title}",
                description=description,
                interaction=interaction,
            )

            embed.set_image(url=specific_comic.image_url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error getting specific xkcd comic: {e}")

            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="An error occurred while fetching a specific xkcd comic",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Xkcd(bot))
