"""Channel selection callback handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from loguru import logger

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


async def _save_channel_selection(wizard: SetupWizardView, channel_attr: str) -> None:
    """Save a specific channel selection to the database immediately."""
    # Map wizard attribute names to database field names
    channel_mapping = {
        "selected_mod_log_channel": "mod_log_id",
        "selected_audit_log_channel": "audit_log_id",
        "selected_join_log_channel": "join_log_id",
        "selected_private_log_channel": "private_log_id",
        "selected_report_log_channel": "report_log_id",
        "selected_dev_log_channel": "dev_log_id",
        "selected_jail_channel": "jail_channel_id",
    }

    db_field = channel_mapping.get(channel_attr)
    if not db_field:
        return

    try:
        channel = getattr(wizard, channel_attr)
        channel_id = channel.id if channel else None

        config_controller = wizard.bot.db.guild_config
        # Ensure config exists, then update it
        await config_controller.get_or_create_config(wizard.guild.id)
        await config_controller.update_config(wizard.guild.id, **{db_field: channel_id})

        logger.info(f"Saved channel selection {channel_attr}={channel_id} for guild {wizard.guild.id}")

    except Exception as e:
        # Log error but don't interrupt the user flow
        logger.error(f"Failed to save channel selection {channel_attr} for guild {wizard.guild.id}: {e}")


async def handle_channel_select(
    interaction: discord.Interaction,
    wizard: SetupWizardView,
    channel_attr: str,
) -> None:
    """Handle channel selection with validation."""
    logger.info(
        f"🔄 Channel selection callback triggered for {channel_attr} by user {interaction.user} in guild {wizard.guild.id}",
    )

    if interaction.user != wizard.author:
        logger.warning(
            f"❌ Unauthorized channel selection attempt by {interaction.user} for {channel_attr} in guild {wizard.guild.id}",
        )
        await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
        return

    # Get selected channel from interaction data
    if not interaction.data or not interaction.guild:
        logger.error(f"❌ Invalid interaction data for channel selection {channel_attr} in guild {wizard.guild.id}")
        await interaction.response.send_message("❌ Invalid interaction data.", ephemeral=True)
        return

    # Store the selection in wizard instance
    selected_channel_id = None
    if selected_channels := interaction.data.get("values", []):
        selected_channel_id = int(selected_channels[0])
        channel = interaction.guild.get_channel(selected_channel_id)
        if isinstance(channel, discord.TextChannel):
            setattr(wizard, channel_attr, channel)
            logger.info(
                f"✅ Stored channel {channel_attr} = {channel.name} ({channel.id}) in wizard for guild {wizard.guild.id}",
            )
        else:
            logger.warning(
                f"⚠️ Selected channel {selected_channel_id} is not a text channel for {channel_attr} in guild {wizard.guild.id}",
            )
            setattr(wizard, channel_attr, None)
    else:
        logger.info(f"🗑️ Cleared channel selection for {channel_attr} in guild {wizard.guild.id}")
        setattr(wizard, channel_attr, None)

    # Save to database immediately
    await _save_channel_selection(wizard, channel_attr)

    await wizard.update_channels_display()
    await interaction.response.edit_message(view=wizard)
    logger.info(f"📝 Updated channel display and message for {channel_attr} in guild {wizard.guild.id}")


async def handle_mod_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle moderation log channel selection."""
    logger.debug(f"📋 Moderation log channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_mod_log_channel")


async def handle_audit_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle audit log channel selection."""
    logger.debug(f"📋 Audit log channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_audit_log_channel")


async def handle_join_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle join log channel selection."""
    logger.debug(f"📋 Join log channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_join_log_channel")


async def handle_private_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle private log channel selection."""
    logger.debug(f"📋 Private log channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_private_log_channel")


async def handle_report_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle report log channel selection."""
    logger.debug(f"📋 Report log channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_report_log_channel")


async def handle_dev_log_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle dev log channel selection."""
    logger.debug(f"📋 Dev log channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_dev_log_channel")


async def handle_jail_channel_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle jail channel selection."""
    logger.debug(f"📋 Jail channel selection for guild {wizard.guild.id}")
    await handle_channel_select(interaction, wizard, "selected_jail_channel")
