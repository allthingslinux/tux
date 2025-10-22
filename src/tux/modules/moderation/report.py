"""
User reporting system for Discord servers.

This module provides an anonymous reporting system that allows users to report
issues, users, or content to server moderators through a modal interface.
"""

import discord
from discord import app_commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.ui.modals.report import ReportModal


class Report(BaseCog):
    """Discord cog for user reporting functionality."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Report cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
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
    """Set up the Report cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Report(bot))
