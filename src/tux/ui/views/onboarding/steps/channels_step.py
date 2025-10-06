"""Channels step for the onboarding wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from ..components.buttons import BackButtonChannels, ContinueButtonChannels
from ..components.selects import (
    AuditLogChannelSelect,
    DevLogChannelSelect,
    JailChannelSelect,
    JoinLogChannelSelect,
    ModLogChannelSelect,
    PrivateLogChannelSelect,
    ReportLogChannelSelect,
)
from .base_step import BaseWizardStep

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


class ChannelsStep(BaseWizardStep):
    """Log channels selection step of the onboarding wizard."""

    def build(self) -> None:
        """Build the channels step."""
        self.clear_items()

        # Main container for channels step
        channels_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x3498DB,  # Blue accent
            id=300,
        )

        # Title
        title_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "# 📋 Step 2: Log Channels",
            id=301,
        )
        channels_container.add_item(title_text)

        # Instructions
        instructions_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Select channels for different types of logging. Each log type needs its own channel.",
            id=302,
        )
        channels_container.add_item(instructions_text)

        self.add_item(channels_container)

        # Add channel selectors in groups to stay under component limits
        self._add_channel_selectors_group_1()  # Mod, Audit, Join logs
        self._add_channel_selectors_group_2()  # Private, Report, Dev logs
        self._add_channel_selectors_group_3()  # Jail

        # Selected channels display container
        self._add_selection_display()

        # Action row with buttons
        self._add_action_buttons()

    def _add_channel_selectors_group_1(self) -> None:
        """Add first group of channel selectors: Moderation, Audit, Join logs."""
        # Group 1 container
        group1_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0xE74C3C,  # Red accent
            id=304,
        )

        group1_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Essential Log Channels**",
            id=305,
        )
        group1_container.add_item(group1_title)

        group1_desc: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Select channels for core server logging. These are the most important logs to set up.",
            id=306,
        )
        group1_container.add_item(group1_desc)

        self.add_item(group1_container)

        # Moderation channel select
        mod_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        mod_select: ModLogChannelSelect = ModLogChannelSelect()
        mod_action_row.add_item(mod_select)
        self.add_item(mod_action_row)

        # Audit channel select
        audit_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        audit_select: AuditLogChannelSelect = AuditLogChannelSelect()
        audit_action_row.add_item(audit_select)
        self.add_item(audit_action_row)

        # Join channel select
        join_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        join_select: JoinLogChannelSelect = JoinLogChannelSelect()
        join_action_row.add_item(join_select)
        self.add_item(join_action_row)

    def _add_channel_selectors_group_2(self) -> None:
        """Add second group of channel selectors: Private, Report, Dev logs."""
        # Group 2 container
        group2_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x9B59B6,  # Purple accent
            id=313,
        )

        group2_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Advanced Log Channels**",
            id=314,
        )
        group2_container.add_item(group2_title)

        group2_desc: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Optional channels for specialized logging. You can skip these if you don't need them.",
            id=315,
        )
        group2_container.add_item(group2_desc)

        self.add_item(group2_container)

        # Private channel select
        private_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        private_select: PrivateLogChannelSelect = PrivateLogChannelSelect()
        private_action_row.add_item(private_select)
        self.add_item(private_action_row)

        # Report channel select
        report_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        report_select: ReportLogChannelSelect = ReportLogChannelSelect()
        report_action_row.add_item(report_select)
        self.add_item(report_action_row)

        # Dev channel select
        dev_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        dev_select: DevLogChannelSelect = DevLogChannelSelect()
        dev_action_row.add_item(dev_select)
        self.add_item(dev_action_row)

    def _add_channel_selectors_group_3(self) -> None:
        """Add third group of channel selectors: Jail channel."""
        # Group 3 container
        group3_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x8E44AD,  # Purple accent
            id=330,
        )

        group3_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Moderation Features**",
            id=331,
        )
        group3_container.add_item(group3_title)

        group3_desc: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Special channel for the jail system where users serve moderation sentences.",
            id=332,
        )
        group3_container.add_item(group3_desc)

        self.add_item(group3_container)

        # Jail channel select
        jail_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()
        jail_select: JailChannelSelect = JailChannelSelect()
        jail_action_row.add_item(jail_select)
        self.add_item(jail_action_row)

    def _add_selection_display(self) -> None:
        """Add selected channels display container."""
        selection_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x2ECC71,  # Green accent for selections
            id=350,
        )

        # Selected channels section
        selection_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Selected Channels:**",
            id=351,
        )
        selection_container.add_item(selection_title)

        self.wizard.selected_channels_text = discord.ui.TextDisplay(
            "No channels selected yet.",
            id=352,
        )
        selection_container.add_item(self.wizard.selected_channels_text)
        self.add_item(selection_container)

    def _add_action_buttons(self) -> None:
        """Add action buttons."""
        # Action row with buttons
        action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow()

        # Continue button
        continue_button: ContinueButtonChannels = ContinueButtonChannels()
        action_row.add_item(continue_button)

        # Back button
        back_button: BackButtonChannels = BackButtonChannels()
        action_row.add_item(back_button)

        self.add_item(action_row)
