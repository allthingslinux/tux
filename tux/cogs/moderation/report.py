import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

import tux.utils.checks as checks
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

        logger.info(f"Received report from {interaction.user.id}")
        if not interaction.guild:
            logger.error("Guild is None")
            return

        logger.info(f"Creating embed for {interaction.user.id}")
        embed = EmbedCreator.create_log_embed(
            title=(f"Anonymous report for {self.short.value}"),  # type: ignore
            description=self.long.value,  # type: ignore
            interaction=None,
        )
        logger.info(f"Embed created for {interaction.user.id}")

        # Get the report log channel ID for the guild
        try:
            logger.info(f"Getting report log channel for guild {interaction.guild.id}")
            report_log_channel_id = await self.config.get_report_log_channel(interaction.guild.id)
        except Exception as e:
            logger.error(f"Failed to get report log channel for guild {interaction.guild.id}. {e}")
            return
        if not report_log_channel_id:
            logger.error(f"Report log channel not set for guild {interaction.guild.id}")
            return

        # Get the report log channel object
        report_log_channel = interaction.guild.get_channel(report_log_channel_id)
        if not report_log_channel or not isinstance(report_log_channel, discord.TextChannel):
            logger.error(f"Failed to get report log channel for guild {interaction.guild.id}")
            return

        # Send confirmation message to user
        logger.info(f"Sending confirmation message to {interaction.user.id}")
        await interaction.response.send_message(
            "Your report has been submitted.",
            ephemeral=True,
        )

        # Send the embed to the report log channel
        logger.info(f"Sending report to {report_log_channel_id}")
        await report_log_channel.send(embed=embed)


class Report(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="report")
    @app_commands.guild_only()
    @checks.has_pl(9)
    async def report(self, interaction: discord.Interaction) -> None:
        """
        Report a user or issue anonymously

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

        modal = ReportModal(bot=self.bot)

        logger.info(f"Opening report modal for {interaction.user.id}")
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Report(bot))
