"""Channel selection callback handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


async def handle_channel_select(
    interaction: discord.Interaction,
    wizard: SetupWizardView,
    channel_attr: str,
) -> None:
    """Handle channel selection with validation."""
    if interaction.user != wizard.author:
        await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
        return

    # Get selected channel from interaction data
    if not interaction.data or not interaction.guild:
        await interaction.response.send_message("❌ Invalid interaction data.", ephemeral=True)
        return

    if selected_channels := interaction.data.get("values", []):
        channel = interaction.guild.get_channel(int(selected_channels[0]))
        if isinstance(channel, discord.TextChannel):
            setattr(wizard, channel_attr, channel)
    else:
        setattr(wizard, channel_attr, None)

    await wizard.update_channels_display()
    await interaction.response.edit_message(view=wizard)


async def handle_mod_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle moderation log channel selection."""
    await handle_channel_select(interaction, wizard, "selected_mod_log_channel")


async def handle_audit_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle audit log channel selection."""
    await handle_channel_select(interaction, wizard, "selected_audit_log_channel")


async def handle_join_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle join log channel selection."""
    await handle_channel_select(interaction, wizard, "selected_join_log_channel")


async def handle_private_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle private log channel selection."""
    await handle_channel_select(interaction, wizard, "selected_private_log_channel")


async def handle_report_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle report log channel selection."""
    await handle_channel_select(interaction, wizard, "selected_report_log_channel")


async def handle_dev_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle dev log channel selection."""
    await handle_channel_select(interaction, wizard, "selected_dev_log_channel")


async def handle_jail_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle jail channel selection."""
    await handle_channel_select(interaction, wizard, "selected_jail_channel")
