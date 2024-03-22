import discord
from discord import app_commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ping(CommandCog):
    @app_commands.command(name="ping", description="Checks the bot's latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """
        Checks the bot's latency.
        """
        discord_ping = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="Pong!",
            description=f"{discord_ping}ms",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Ping(bot))
