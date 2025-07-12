import discord
from bot import Tux
from discord import app_commands
from discord.ext import commands
from ui.modals.report import ReportModal


class Report(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @app_commands.command(name="report")
    @app_commands.guild_only()
    async def report(self, interaction: discord.Interaction) -> None:
        """
        Report a user or issue anonymously

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        modal = ReportModal(bot=self.bot)

        await interaction.response.send_modal(modal)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Report(bot))
