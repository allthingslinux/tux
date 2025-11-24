"""
Discord Report Modal for Tux Bot.

This module provides a modal dialog for users to submit anonymous reports
to the server moderation team with proper logging and thread creation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from loguru import logger

from tux.database.utils import get_db_controller_from
from tux.ui.embeds import EmbedCreator

if TYPE_CHECKING:
    from tux.core.bot import Tux


class ReportModal(discord.ui.Modal):
    """Modal for submitting anonymous user reports."""

    def __init__(self, *, title: str = "Submit an anonymous report", bot: Tux) -> None:
        """Initialize the report modal.

        Parameters
        ----------
        title : str, optional
            The modal title, by default "Submit an anonymous report".
        bot : Tux
            The bot instance to use for database access and operations.

        Raises
        ------
        RuntimeError
            If DatabaseService is not available via DI.
        """
        super().__init__(title=title)
        self.bot = bot
        # Resolve config via shared DB utility (strict DI required)
        controller = get_db_controller_from(self.bot, fallback_to_direct=False)
        if controller is None:
            error_msg = "DatabaseService not available. DI is required for ReportModal"
            raise RuntimeError(error_msg)
        self.config = controller.guild_config

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
        Send the report to the moderation team.

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
            report_log_channel_id = await self.config.get_report_log_id(
                interaction.guild.id,
            )
        except Exception as e:
            logger.error(
                f"Failed to get report log channel for guild {interaction.guild.id}. {e}",
            )
            await interaction.response.send_message(
                "Failed to submit your report. Please try again later.",
                ephemeral=True,
            )
            return

        if not report_log_channel_id:
            logger.error(f"Report log channel not set for guild {interaction.guild.id}")
            await interaction.response.send_message(
                "The report log channel has not been set up. Please contact an administrator.",
                ephemeral=True,
            )
            return

        # Get the report log channel object
        report_log_channel = interaction.guild.get_channel(report_log_channel_id)
        if not report_log_channel or not isinstance(
            report_log_channel,
            discord.TextChannel,
        ):
            logger.error(
                f"Failed to get report log channel for guild {interaction.guild.id}",
            )
            await interaction.response.send_message(
                "Failed to submit your report. Please try again later.",
                ephemeral=True,
            )
            return

        # Send confirmation message to user
        await interaction.response.send_message(
            "Your report has been submitted.",
            ephemeral=True,
        )

        message = await report_log_channel.send(embed=embed)
        await report_log_channel.create_thread(
            name=f"Anonymous report for {self.short.value}",  # type: ignore
            message=message,
            auto_archive_duration=10080,
        )
