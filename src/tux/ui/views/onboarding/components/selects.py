"""Select components for the onboarding wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from .base import WizardComponent

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView  # noqa: F401


class ModLogChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Moderation log channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose moderation log channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=316,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle moderation log channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_mod_log_channel_select(interaction)


class AuditLogChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Audit log channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose audit log channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=317,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle audit log channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_audit_log_channel_select(interaction)


class JoinLogChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Join log channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose join/leave log channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=318,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle join log channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_join_log_channel_select(interaction)


class PrivateLogChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Private log channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose private log channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=333,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle private log channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_private_log_channel_select(interaction)


class ReportLogChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Report log channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose report log channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=334,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle report log channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_report_log_channel_select(interaction)


class DevLogChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Dev log channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose dev log channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=335,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle dev log channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_dev_log_channel_select(interaction)


class JailChannelSelect(WizardComponent, discord.ui.ChannelSelect["SetupWizardView"]):
    """Jail channel select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose jail channel...",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            id=336,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle jail channel selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_jail_channel_select(interaction)


class PermissionRankRoleSelect(WizardComponent, discord.ui.RoleSelect["SetupWizardView"]):
    """Permission rank role select."""

    def __init__(self, rank: int, rank_name: str, placeholder: str | None = None) -> None:
        self.rank = rank
        self.rank_name = rank_name
        super().__init__(
            placeholder=placeholder or f"Choose {rank_name} roles...",
            min_values=0,
            max_values=10,
            id=400 + rank,  # Unique ID based on rank
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle permission rank role selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        if method := getattr(wizard_view, "on_permission_rank_role_select", None):
            await method(interaction, self.rank, self.values)


class JailRoleSelect(WizardComponent, discord.ui.RoleSelect["SetupWizardView"]):
    """Jail role select."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose jail role...",
            min_values=0,
            max_values=1,
            id=423,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle jail role selection."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await wizard_view.on_jail_role_select(interaction)
