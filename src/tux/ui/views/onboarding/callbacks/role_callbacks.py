"""Role selection callback handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from loguru import logger

from tux.core.permission_system import get_permission_system

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


async def handle_role_select(
    interaction: discord.Interaction,
    wizard: SetupWizardView,
    role_attr: str,
    is_single: bool = False,
) -> None:
    """Handle role selection with validation."""
    if interaction.user != wizard.author:
        await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
        return

    # Get selected role from interaction data
    if not interaction.data or not interaction.guild:
        await interaction.response.send_message("❌ Invalid interaction data.", ephemeral=True)
        return

    selected_role_ids = interaction.data.get("values", [])

    if is_single:
        # Single role selection
        if selected_role_ids:
            role = interaction.guild.get_role(int(selected_role_ids[0]))
            if role:
                setattr(wizard, role_attr, role)
        else:
            setattr(wizard, role_attr, None)
    else:
        # Multiple role selection
        roles = []
        for role_id in selected_role_ids:
            role = interaction.guild.get_role(int(role_id))
            if role:
                roles.append(role)
        setattr(wizard, role_attr, roles)

    # Update the roles display
    wizard.update_roles_display()

    await interaction.response.edit_message(view=wizard)


async def handle_jail_role_select(interaction: discord.Interaction, wizard: SetupWizardView) -> None:
    """Handle jail role selection."""
    await handle_role_select(interaction, wizard, "selected_jail_role", is_single=True)


async def handle_permission_rank_role_select(
    interaction: discord.Interaction,
    wizard: SetupWizardView,
    rank: int,
    roles: list[discord.Role],
) -> None:
    """Handle permission rank role selection."""
    if interaction.user != wizard.author:
        await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
        return

    if not interaction.guild:
        await interaction.response.send_message("❌ Invalid guild context.", ephemeral=True)
        return

    try:
        # Get permission system
        permission_system = get_permission_system()

        # Assign each role to the permission rank
        # First remove any existing assignments for these roles to avoid duplicates
        for role in roles:
            await permission_system.remove_role_assignment(interaction.guild.id, role.id)

        # Then assign each role to the new permission rank
        for role in roles:
            await permission_system.assign_permission_rank(
                guild_id=interaction.guild.id,
                rank=rank,
                role_id=role.id,
                assigned_by=interaction.user.id,
            )

        # Store roles in wizard instance for display
        wizard.selected_permission_roles[rank] = roles

        logger.info(f"Assigned rank {rank} to {len(roles)} roles in guild {interaction.guild.id}")

        # Update the roles display
        wizard.update_roles_display()

        await interaction.response.edit_message(view=wizard)

    except Exception as e:
        logger.error(f"Failed to assign permission rank {rank} to roles: {e}")
        await interaction.response.send_message(f"❌ Failed to assign permission rank: {e}", ephemeral=True)
