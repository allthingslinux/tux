import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.embeds import EmbedCreator


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Checks the bot's latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        discord_ping = round(self.bot.latency * 1000)

        embed = EmbedCreator.create_success_embed(
            title="Pong!", description=f"{discord_ping}ms", interaction=interaction
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
