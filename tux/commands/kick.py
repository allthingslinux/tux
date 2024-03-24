import discord
from discord import app_commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Kick(CommandCog):
    @app_commands.command(name="kick", description="Kicks a user from the server.")
    async def kick(self, interaction: discord.Interaction) -> None:
        """
        Kicks a user from the server.
        """
        await interaction.response.send_message("Kick command is not implemented yet.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Kick(bot))
