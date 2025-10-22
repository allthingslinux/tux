"""Simple start view for onboarding."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from loguru import logger

if TYPE_CHECKING:
    from tux.core.bot import Tux


class OnboardingStartView(discord.ui.View):
    """View for starting the onboarding process."""

    def __init__(self, bot: Tux, guild: discord.Guild) -> None:
        """Initialize the onboarding start view.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        guild : discord.Guild
            The guild to set up.
        """
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild

    @discord.ui.button(label="🚀 Start Setup", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def start_setup(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        """Start the setup wizard."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                "❌ Only the server owner can start the setup wizard.",
                ephemeral=True,
            )
            return

        try:
            # Import here to avoid circular imports
            from .wizard import SetupWizardView  # noqa: PLC0415

            author = cast(discord.User, interaction.user)
            view = SetupWizardView(self.bot, interaction.guild, author)

            await interaction.response.send_message(view=view)

        except Exception as e:
            logger.error(f"Failed to start setup wizard: {e}")
            await interaction.response.send_message(f"❌ Failed to start setup wizard: {e}", ephemeral=True)
