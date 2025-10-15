import discord
from discord import app_commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.ui.modals.report import ReportModal


class Report(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @app_commands.command(name="report")
    @app_commands.guild_only()
    async def report(self, interaction: discord.Interaction) -> None:
        """
        Report a user or issue anonymously.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """
        modal = ReportModal(bot=self.bot)

        await interaction.response.send_modal(modal)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Report(bot))
