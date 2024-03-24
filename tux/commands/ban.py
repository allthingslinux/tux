import discord
from discord import app_commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ban(CommandCog):
    @app_commands.command(name="ban", description="Bans a user from the server.")
    async def ban(self, interaction: discord.Interaction) -> None:
        """
        Bans a user from the server.
        """
        await interaction.response.send_message("Ban command is not implemented yet.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Ban(bot))
