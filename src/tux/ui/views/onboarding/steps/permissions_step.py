"""Permissions step for the onboarding wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from ..components.buttons import BackButtonPermissions, ContinueButton
from .base_step import BaseWizardStep

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


class PermissionsStep(BaseWizardStep):
    """Permissions initialization step of the onboarding wizard."""

    def build(self) -> None:
        """Build the permissions step."""
        self.clear_items()

        # Main container for permissions step
        permissions_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0xFF6B35,  # Orange accent
            id=200,
        )

        # Title
        title_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "# 🔐 Step 1: Permission System",
            id=201,
        )
        permissions_container.add_item(title_text)

        # Description
        description_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Setting up the permission system for your server...",
            id=202,
        )
        permissions_container.add_item(description_text)

        # Add separator
        separator: discord.ui.Separator[SetupWizardView] = discord.ui.Separator(
            id=203,
        )
        permissions_container.add_item(separator)

        # Status section
        status_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Status:**",
            id=204,
        )
        permissions_container.add_item(status_title)

        self.wizard.status_text = discord.ui.TextDisplay(
            "Initializing permission ranks...",
            id=205,
        )
        permissions_container.add_item(self.wizard.status_text)

        self.add_item(permissions_container)

        # Action row with buttons
        action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()

        # Continue button (initially disabled)
        self.wizard.continue_button = ContinueButton()
        action_row.add_item(self.wizard.continue_button)

        # Back button
        back_button: BackButtonPermissions = BackButtonPermissions()
        action_row.add_item(back_button)

        self.add_item(action_row)
