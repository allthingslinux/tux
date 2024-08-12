import discord
from discord import app_commands
from discord.ext import commands

from tux.ui.modals.suggestion import SuggestionModal


class Suggestion(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="suggest")
    @app_commands.guild_only()
    async def suggestion(self, interaction: discord.Interaction) -> None:
        """
        Submit a suggestion for a server

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        modal = SuggestionModal(bot=self.bot)

        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Suggestion(bot))
