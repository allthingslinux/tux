import traceback

import discord
from discord import app_commands
from discord.ext import commands


class ReportModal(discord.ui.Modal, title="Report"):
    report = discord.ui.TextInput(  # type: ignore
        label="Submit your anonymous report",
        style=discord.TextStyle.long,
        placeholder="Type your feedback here...",
        required=True,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Thanks for your report and helping keep our community safe!",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Oops! Something went wrong.", ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


class Report(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="report", description="Make an anonymous report")
    async def report(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(ReportModal())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Report(bot))
