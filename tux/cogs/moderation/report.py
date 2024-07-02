import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class ReportModal(discord.ui.Modal):
    def __init__(self, *, title: str = "Submit an anonymous report", bot: commands.Bot) -> None:
        super().__init__(title=title)
        self.bot = bot
        self.channel = CONST.LOG_CHANNELS["REPORTS"]

    short = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.short,
        label="Related user(s) or issue(s)",
        required=True,
        max_length=100,
        placeholder="User IDs, usernames, or brief description",
    )

    long = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.long,
        label="Your report",
        required=True,
        max_length=4000,
        placeholder="Please provide as much detail as possible",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Sends the report to the moderation team.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        embed = EmbedCreator.create_log_embed(
            title=(f"Anonymous report for {self.short.value}"),  # type: ignore
            description=self.long.value,  # type: ignore
            interaction=None,
        )

        channel = self.bot.get_channel(self.channel) or await self.bot.fetch_channel(self.channel)
        if isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Your report has been submitted.", ephemeral=True)
            await channel.send(embed=embed)


class Report(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="report", description="Report a user or issue anonymously")
    async def report(self, interaction: discord.Interaction) -> None:
        """
        Opens the report modal for users to submit an anonymous report.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        modal = ReportModal(bot=self.bot)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Report(bot))
