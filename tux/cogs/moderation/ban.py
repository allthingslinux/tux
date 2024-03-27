import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ban", description="Bans a user from the server.")
    async def ban(self, interaction: discord.Interaction) -> None:
        logger.info(f"{interaction.user} used the ban command in {interaction.channel}.")

        await interaction.response.send_message("Ban command is not implemented yet.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
