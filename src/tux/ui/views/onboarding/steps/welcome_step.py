"""Welcome step for the onboarding wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from ..components.buttons import CancelButton, StartButton
from .base_step import BaseWizardStep

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


class WelcomeStep(BaseWizardStep):
    """Welcome step of the onboarding wizard."""

    def build(self) -> None:
        """Build the welcome step."""
        # Clear existing items
        self.clear_items()

        # Main container for the welcome step
        welcome_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x00FF00,  # Green accent
            id=100,
        )

        # Welcome message
        welcome_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "# 🎉 Welcome to Tux Setup!\n\n"
            "I'll help you configure your server for moderation and management.\n"
            "This wizard will guide you through:",
            id=101,
        )
        welcome_container.add_item(welcome_text)

        # Add separator for visual spacing
        separator: discord.ui.Separator[SetupWizardView] = discord.ui.Separator(
            id=102,
        )
        welcome_container.add_item(separator)

        # Steps list
        steps_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Setup Steps:**",
            id=103,
        )
        welcome_container.add_item(steps_title)

        step1_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "1. **Permission System** - Set up command permissions",
            id=104,
        )
        welcome_container.add_item(step1_text)

        step2_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "2. **Log Channels** - Choose where to log moderation actions",
            id=105,
        )
        welcome_container.add_item(step2_text)

        step3_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "3. **Staff Roles** - Assign roles to permission levels",
            id=106,
        )
        welcome_container.add_item(step3_text)

        step4_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "4. **Finalization** - Complete the setup",
            id=107,
        )
        welcome_container.add_item(step4_text)

        # Final prompt
        prompt_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "\n**Ready to get started?**",
            id=108,
        )
        welcome_container.add_item(prompt_text)

        self.add_item(welcome_container)

        # Action row with buttons
        action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()

        # Start button
        start_button: StartButton = StartButton()
        action_row.add_item(start_button)

        # Cancel button
        cancel_button: CancelButton = CancelButton()
        action_row.add_item(cancel_button)

        self.add_item(action_row)
