"""Role selection callback handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from loguru import logger

from tux.core.permission_system import get_permission_system

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


async def _save_jail_role_selection(wizard: SetupWizardView) -> None:
    """Save jail role selection to the database immediately."""
    try:
        role = wizard.selected_jail_role
        role_id = role.id if role else None

        config_controller = wizard.bot.db.guild_config
        # Ensure config exists, then update it
        await config_controller.get_or_create_config(wizard.guild.id)
        await config_controller.update_config(wizard.guild.id, jail_role_id=role_id)

        logger.info(f"Saved jail role selection {role_id} for guild {wizard.guild.id}")

    except Exception as e:
        # Log error but don't interrupt the user flow
        logger.error(f"Failed to save jail role selection for guild {wizard.guild.id}: {e}")


async def handle_role_select(
    interaction: discord.Interaction,
    wizard: SetupWizardView,
    role_attr: str,
    is_single: bool = False,
) -> None:
    """Handle role selection with validation."""
    logger.info(
        f"🔄 Role selection callback triggered for {role_attr} by user {interaction.user} in guild {wizard.guild.id}",
    )

    if interaction.user != wizard.author:
        logger.warning(
            f"❌ Unauthorized role selection attempt by {interaction.user} for {role_attr} in guild {wizard.guild.id}",
        )
        await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
        return

    # Get selected role from interaction data
    if not interaction.data or not interaction.guild:
        logger.error(f"❌ Invalid interaction data for role selection {role_attr} in guild {wizard.guild.id}")
        await interaction.response.send_message("❌ Invalid interaction data.", ephemeral=True)
        return

    selected_role_ids = interaction.data.get("values", [])
    logger.debug(f"📋 Processing {len(selected_role_ids)} role selections for {role_attr} in guild {wizard.guild.id}")

    if is_single:
        # Single role selection
        if selected_role_ids:
            role_id = int(selected_role_ids[0])
            if role := interaction.guild.get_role(role_id):
                setattr(wizard, role_attr, role)
                logger.info(
                    f"✅ Stored single role {role_attr} = {role.name} ({role.id}) in wizard for guild {wizard.guild.id}",
                )
            else:
                logger.warning(f"⚠️ Role {role_id} not found for {role_attr} in guild {wizard.guild.id}")
                setattr(wizard, role_attr, None)
        else:
            logger.info(f"🗑️ Cleared single role selection for {role_attr} in guild {wizard.guild.id}")
            setattr(wizard, role_attr, None)

        # Save jail role immediately if that's what was selected
        if role_attr == "selected_jail_role":
            await _save_jail_role_selection(wizard)
    else:
        # Multiple role selection
        roles: list[discord.Role] = []

        for role_id in selected_role_ids:
            role_id_int = int(role_id)
            if role := interaction.guild.get_role(role_id_int):
                roles.append(role)
                logger.debug(f"✅ Added role {role.name} ({role.id}) to {role_attr} selection")
            else:
                logger.warning(f"⚠️ Role {role_id_int} not found for {role_attr} in guild {wizard.guild.id}")

        setattr(wizard, role_attr, roles)
        logger.info(f"✅ Stored {len(roles)} roles for {role_attr} in wizard for guild {wizard.guild.id}")

    # Update the roles display
    wizard.update_roles_display()
    await interaction.response.edit_message(view=wizard)
    logger.info(f"📝 Updated role display and message for {role_attr} in guild {wizard.guild.id}")


async def handle_jail_role_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle jail role selection."""
    logger.debug(f"🔒 Jail role selection for guild {wizard.guild.id}")
    await handle_role_select(interaction, wizard, "selected_jail_role", is_single=True)


async def handle_permission_rank_role_select(
    interaction: discord.Interaction,
    wizard: SetupWizardView,
    rank: int,
    roles: list[discord.Role],
) -> None:
    """Handle permission rank role selection."""
    logger.info(
        f"🔄 Permission rank role selection callback triggered for rank {rank} with {len(roles)} roles by user {interaction.user} in guild {wizard.guild.id}",
    )

    if interaction.user != wizard.author:
        logger.warning(
            f"❌ Unauthorized permission rank selection attempt by {interaction.user} for rank {rank} in guild {wizard.guild.id}",
        )
        await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
        return

    if not interaction.guild:
        logger.error(f"❌ Invalid guild context for permission rank {rank} selection in guild {wizard.guild.id}")
        await interaction.response.send_message("❌ Invalid guild context.", ephemeral=True)
        return

    try:
        logger.debug(
            f"🔧 Processing permission rank {rank} assignment for {len(roles)} roles in guild {interaction.guild.id}",
        )

        # Get permission system
        permission_system = get_permission_system()

        # Assign each role to the permission rank
        # First remove any existing assignments for these roles to avoid duplicates
        logger.debug(f"🧹 Removing existing assignments for {len(roles)} roles from rank {rank}")
        for role in roles:
            await permission_system.remove_role_assignment(interaction.guild.id, role.id)

        # Then assign each role to the new permission rank
        logger.debug(f"✅ Assigning {len(roles)} roles to permission rank {rank}")
        for role in roles:
            await permission_system.assign_permission_rank(
                guild_id=interaction.guild.id,
                rank=rank,
                role_id=role.id,
                assigned_by=interaction.user.id,
            )
            logger.debug(f"✅ Assigned role {role.name} ({role.id}) to rank {rank}")

        # Store roles in wizard instance for display
        wizard.selected_permission_roles[rank] = roles

        logger.info(f"🎯 Successfully assigned rank {rank} to {len(roles)} roles in guild {interaction.guild.id}")

        # Update the roles display
        wizard.update_roles_display()
        await interaction.response.edit_message(view=wizard)
        logger.info(f"📝 Updated role display and message for rank {rank} in guild {wizard.guild.id}")

    except Exception as e:
        logger.error(f"❌ Failed to assign permission rank {rank} to roles in guild {wizard.guild.id}: {e}")
        await interaction.response.send_message(f"❌ Failed to assign permission rank: {e}", ephemeral=True)
