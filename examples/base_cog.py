import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST


class BaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.color = CONST.COLORS["INFO"]

    """
      Example app command:
      @app_commands.command(name="example", description="An example app command.")
      async def example(self, interaction: discord.Interaction) -> None:
          await interaction.response.send_message("This is an example app command message response.")
          logger.info(f"{interaction.user} used the example command in {interaction.channel}.")
      
      Example prefix command:
      @commands.command(name="ex", description="An example command.")
      async def ex(self, ctx: commands.Context[commands.Bot]) -> None:
          await ctx.send("This is an example command message response.")
          logger.info(f"{ctx.author} used the example command in {ctx.channel}.") 
    """


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BaseCog(bot))
