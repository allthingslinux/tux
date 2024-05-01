import discord
import psutil
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Checks the bot's latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """
        Check the bot's latency and other stats.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        # Get the latency of the bot in milliseconds
        discord_ping = round(self.bot.latency * 1000)

        # Get the CPU usage and RAM usage of the bot
        cpu_usage = psutil.cpu_percent()
        ram_amount = psutil.virtual_memory().used

        # Format the RAM usage to be in GB or MB
        if ram_amount >= 1024**3:
            ram_amount_formatted = f"{ram_amount // (1024**3)}GB"
        else:
            ram_amount_formatted = f"{ram_amount // (1024**2)}MB"

        embed = EmbedCreator.create_success_embed(
            title="Pong!", description="Here are some stats about the bot.", interaction=interaction
        )

        embed.add_field(name="API Latency", value=f"{discord_ping}ms", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM Usage", value=f"{ram_amount_formatted}", inline=True)

        await interaction.response.send_message(embed=embed)

        logger.info(f"{interaction.user} used the ping command in {interaction.channel}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
