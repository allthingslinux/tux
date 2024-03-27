import discord
from discord.ext import commands
from loguru import logger


class CommandEventsCog(commands.Cog, name="Command Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ) -> None:
        logger.info(
            f"'{command.name}' command was used by {interaction.user} in {interaction.channel}."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommandEventsCog(bot))
