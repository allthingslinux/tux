"""Completion step for the onboarding wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from ..components.buttons import FinishButton
from .base_step import BaseWizardStep

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


class CompletionStep(BaseWizardStep):
    """Completion step of the onboarding wizard."""

    def build(self) -> None:
        """Build the completion step."""
        self.clear_items()

        # Main container for completion step
        completion_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x00FF00,  # Green accent for success
            id=500,
        )

        # Success title
        success_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "# ✅ Setup Complete!",
            id=501,
        )
        completion_container.add_item(success_title)

        # Description
        description_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Your server has been successfully configured:",
            id=502,
        )
        completion_container.add_item(description_text)

        # Add separator
        separator: discord.ui.Separator[SetupWizardView] = discord.ui.Separator(
            id=503,
        )
        completion_container.add_item(separator)

        # Configuration summary section
        summary_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Configuration Summary:**",
            id=504,
        )
        completion_container.add_item(summary_title)

        permission_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "✅ **Permission System:** Initialized",
            id=505,
        )
        completion_container.add_item(permission_text)

        # Calculate selected channels count
        selected_count = sum(
            ch is not None
            for ch in [
                self.wizard.selected_mod_log_channel,
                self.wizard.selected_audit_log_channel,
                self.wizard.selected_join_log_channel,
                self.wizard.selected_private_log_channel,
                self.wizard.selected_report_log_channel,
                self.wizard.selected_dev_log_channel,
                self.wizard.selected_jail_channel,
            ]
        )
        channels_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            f"✅ **Log Channels:** {selected_count} selected",
            id=506,
        )
        completion_container.add_item(channels_text)

        roles_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "✅ **Permission Ranks:** Roles assigned to ranks 1-7",
            id=507,
        )
        completion_container.add_item(roles_text)

        jail_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            f"✅ **Jail Role:** {'Assigned' if self.wizard.selected_jail_role else 'Not assigned'}",
            id=508,
        )
        completion_container.add_item(jail_text)

        # Final message
        final_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "\n**Your server is now ready to use Tux!** 🚀",
            id=511,
        )
        completion_container.add_item(final_text)

        self.add_item(completion_container)

        # Action row with finish button
        action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()

        # Finish button
        finish_button: FinishButton = FinishButton()
        action_row.add_item(finish_button)

        self.add_item(action_row)
