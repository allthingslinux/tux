import discord
from bot import Tux
from database.controllers import DatabaseController
from loguru import logger
from ui.embeds import EmbedCreator


class ReportModal(discord.ui.Modal):
    def __init__(self, *, title: str = "Submit an anonymous report", bot: Tux) -> None:
        super().__init__(title=title)
        self.bot = bot
        self.config = DatabaseController().guild_config

    short = discord.ui.TextInput(  # type: ignore
        label="Related user(s) or issue(s)",
        style=discord.TextStyle.short,
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
            logger.error("Guild is None")
            return

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name="tux",
            title=(f"Anonymous report for {self.short.value}"),  # type: ignore
            description=self.long.value,  # type: ignore
        )

        try:
            report_log_channel_id = await self.config.get_report_log_id(interaction.guild.id)
        except Exception as e:
            logger.error(f"Failed to get report log channel for guild {interaction.guild.id}. {e}")
            await interaction.response.send_message(
                "Failed to submit your report. Please try again later.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if not report_log_channel_id:
            logger.error(f"Report log channel not set for guild {interaction.guild.id}")
            await interaction.response.send_message(
                "The report log channel has not been set up. Please contact an administrator.",
                ephemeral=True,
                delete_after=30,
            )
            return

        # Get the report log channel object
        report_log_channel = interaction.guild.get_channel(report_log_channel_id)
        if not report_log_channel or not isinstance(report_log_channel, discord.TextChannel):
            logger.error(f"Failed to get report log channel for guild {interaction.guild.id}")
            await interaction.response.send_message(
                "Failed to submit your report. Please try again later.",
                ephemeral=True,
                delete_after=30,
            )
            return

        # Send confirmation message to user
        await interaction.response.send_message(
            "Your report has been submitted.",
            ephemeral=True,
            delete_after=30,
        )

        message = await report_log_channel.send(embed=embed)
        await report_log_channel.create_thread(
            name=f"Anonymous report for {self.short.value}",  # type: ignore
            message=message,
            auto_archive_duration=10080,
        )
