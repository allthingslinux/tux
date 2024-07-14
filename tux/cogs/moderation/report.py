import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator


class ReportModal(discord.ui.Modal):
    def __init__(self, *, title: str = "Submit an anonymous report", bot: commands.Bot) -> None:
        super().__init__(title=title)
        self.bot = bot
        self.config = DatabaseController().guild_config

    short = discord.ui.TextInput(  # type: ignore
        style=discord.TextStyle.short,
        label="Related user(s) or issue(s)",
        required=True,
        max_length=100,
        placeholder="User IDs, usernames, or a brief description",
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
        if not interaction.guild:
            return

        embed = EmbedCreator.create_log_embed(
            title=(f"Anonymous report for {self.short.value}"),  # type: ignore
            description=self.long.value,  # type: ignore
            interaction=None,
        )

        # Get the report log channel ID for the guild
        try:
            report_log_channel_id = await self.config.get_mod_log_channel(interaction.guild.id)
        except Exception as e:
            logger.error(f"Failed to get mod log channel for guild {interaction.guild.id}. {e}")
            return
        if not report_log_channel_id:
            return

        # Get the report log channel object
        report_log_channel = interaction.guild.get_channel(report_log_channel_id)
        if not report_log_channel or not isinstance(report_log_channel, discord.TextChannel):
            return

        # Send confirmation message to user
        await interaction.response.send_message(
            "Your report has been submitted.",
            ephemeral=True,
        )

        # Send the embed to the report log channel
        await report_log_channel.send(embed=embed)


class Report(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="report", description="Report a user or issue anonymously")
    @app_commands.guild_only()
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
