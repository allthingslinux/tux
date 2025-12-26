"""
Callback utilities for ConfigDashboard.

Provides reusable patterns for authorization checks, error handling,
and cache invalidation in callback functions.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

from tux.core.permission_system import RESTRICTED_COMMANDS
from tux.database.models.models import PermissionAssignment, PermissionCommand

from .modals import EditRankModal

if TYPE_CHECKING:
    from .dashboard import ConfigDashboard


async def validate_author(
    interaction: discord.Interaction,
    author: discord.User | discord.Member,
    error_message: str,
) -> bool:
    """
    Validate that the interaction user is the authorized author.

    Parameters
    ----------
    interaction : discord.Interaction
        The interaction to validate
    author : discord.User | discord.Member
        The authorized author
    error_message : str
        Error message to send if validation fails

    Returns
    -------
    bool
        True if authorized, False otherwise
    """
    if interaction.user != author:
        await interaction.response.send_message(error_message, ephemeral=True)
        return False
    return True


async def validate_interaction_data(interaction: discord.Interaction) -> bool:
    """
    Validate that interaction has valid data.

    Parameters
    ----------
    interaction : discord.Interaction
        The interaction to validate

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if not interaction.data:
        await interaction.response.send_message(
            "❌ Invalid interaction data",
            ephemeral=True,
        )
        return False
    return True


async def handle_callback_error(
    interaction: discord.Interaction,
    error: Exception,
    operation: str,
    context: str = "",
) -> None:
    """
    Handle errors in callback functions with consistent error messages.

    Parameters
    ----------
    interaction : discord.Interaction
        The interaction that triggered the error
    error : Exception
        The exception that occurred
    operation : str
        Description of the operation that failed
    context : str, optional
        Additional context for the error message
    """
    logger.error(f"Error {operation} {context}: {error}", exc_info=True)
    error_msg = f"❌ Error {operation}: {error}"
    try:
        if interaction.response.is_done():
            await interaction.followup.send(error_msg, ephemeral=True)
        else:
            await interaction.response.send_message(error_msg, ephemeral=True)
    except Exception as send_error:
        logger.error(f"Failed to send error message: {send_error}")


async def invalidate_and_rebuild(
    dashboard: ConfigDashboard,
    mode: str,
    rebuild_method: Callable[[], Awaitable[None]],
    interaction: discord.Interaction,
) -> None:
    """
    Invalidate cache, rebuild mode, and update message.

    Parameters
    ----------
    dashboard : ConfigDashboard
        The dashboard instance
    mode : str
        The mode to rebuild
    rebuild_method : Callable[[], Awaitable[None]]
        Async method to rebuild the mode
    interaction : discord.Interaction
        The interaction to update the message for
    """
    dashboard.invalidate_cache()
    dashboard.current_mode = mode
    await rebuild_method()
    if interaction.message:
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            view=dashboard,
        )


def create_authorized_callback(
    dashboard: ConfigDashboard,
    callback_func: Callable[[discord.Interaction], Awaitable[None]],
    unauthorized_message: str = "❌ You are not authorized to perform this action.",
) -> Callable[[discord.Interaction], Awaitable[None]]:
    """
    Wrap a callback function with authorization checks.

    Parameters
    ----------
    dashboard : ConfigDashboard
        The dashboard instance
    callback_func : Callable[[discord.Interaction], Awaitable[None]]
        The callback function to wrap
    unauthorized_message : str
        Message to send if user is not authorized

    Returns
    -------
    Callable[[discord.Interaction], Awaitable[None]]
        Wrapped callback with authorization checks
    """

    async def wrapped_callback(interaction: discord.Interaction) -> None:
        if not await validate_author(
            interaction,
            dashboard.author,
            unauthorized_message,
        ):
            return
        if not await validate_interaction_data(interaction):
            return
        await callback_func(interaction)

    return wrapped_callback


def create_role_update_callback(
    dashboard: ConfigDashboard,
    rank_value: int,
    rank_db_id: int,
) -> Any:
    """Create a callback for role selection that updates the database based on new state."""

    async def callback(interaction: discord.Interaction) -> None:
        """Handle role selection update."""
        if not await validate_author(
            interaction,
            dashboard.author,
            "❌ You are not authorized to modify role assignments.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        try:
            # Get selected role IDs from interaction
            selected_role_ids: set[int] = set()
            if interaction.data:
                values = interaction.data.get("values", [])
                selected_role_ids = {int(role_id) for role_id in values}

            # Get current assignments for this rank
            existing_assignments = (
                await dashboard.bot.db.permission_assignments.get_assignments_by_guild(
                    dashboard.guild.id,
                )
            )
            current_role_ids = {
                assignment.role_id
                for assignment in existing_assignments
                if assignment.permission_rank_id == rank_db_id
            }

            # Calculate changes
            roles_to_add = selected_role_ids - current_role_ids
            roles_to_remove = current_role_ids - selected_role_ids

            # Apply changes
            added_count = 0
            removed_count = 0

            # Add new roles
            for role_id in roles_to_add:
                await dashboard.bot.db.permission_assignments.assign_permission_rank(
                    dashboard.guild.id,
                    rank_db_id,
                    role_id,
                )
                added_count += 1

            # Remove unselected roles
            for role_id in roles_to_remove:
                deleted_count = (
                    await dashboard.bot.db.permission_assignments.delete_where(
                        filters=(
                            PermissionAssignment.guild_id == dashboard.guild.id,
                            PermissionAssignment.permission_rank_id == rank_db_id,
                            PermissionAssignment.role_id == role_id,
                        ),
                    )
                )
                if deleted_count > 0:
                    removed_count += 1

            # Build response message
            if added_count > 0 and removed_count > 0:
                message = f"✅ Updated Rank {rank_value}: Added {added_count} role(s), removed {removed_count} role(s)"
            elif added_count > 0:
                message = f"✅ Added {added_count} role(s) to Rank {rank_value}"
            elif removed_count > 0:
                message = f"✅ Removed {removed_count} role(s) from Rank {rank_value}"
            else:
                message = f"✅ Rank {rank_value} roles unchanged"

            await interaction.response.send_message(message, ephemeral=True)

            # Invalidate cache and rebuild to show updated assignments
            await invalidate_and_rebuild(
                dashboard,
                "roles",
                dashboard.build_roles_mode,
                interaction,
            )

        except Exception as e:
            await handle_callback_error(
                interaction,
                e,
                "updating roles",
                f"for rank {rank_value}",
            )

    return callback


def create_command_rank_callback(dashboard: ConfigDashboard, command_name: str) -> Any:
    """Create a callback for command rank assignment."""

    async def callback(interaction: discord.Interaction) -> None:
        """Handle command rank selection."""
        if not await validate_author(
            interaction,
            dashboard.author,
            "❌ You are not authorized to modify command permissions.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        # Block restricted commands from being assigned to ranks
        if command_name.lower() in RESTRICTED_COMMANDS:
            await interaction.response.send_message(
                f"❌ Cannot assign permission rank to `{command_name}`. "
                "This command is restricted to bot owners and sysadmins only.",
                ephemeral=True,
            )
            return

        try:
            values = interaction.data.get("values", [])  # type: ignore[index]
            selected_value = values[0] if values else None

            if selected_value == "unassign":
                # Remove command permission
                await dashboard.bot.db.command_permissions.delete_where(
                    filters=(
                        PermissionCommand.guild_id == dashboard.guild.id,
                        PermissionCommand.command_name == command_name,
                    ),
                )
                message = f"✅ Command `{command_name}` unassigned (now disabled)"
            elif selected_value is not None:
                # Assign rank to command
                rank_value = int(selected_value)

                # Validate rank exists
                ranks = await dashboard.bot.db.permission_ranks.get_permission_ranks_by_guild(
                    dashboard.guild.id,
                )
                rank_obj = next((r for r in ranks if r.rank == rank_value), None)
                if not rank_obj:
                    await interaction.response.send_message(
                        f"❌ Rank {rank_value} does not exist.",
                        ephemeral=True,
                    )
                    return

                await dashboard.bot.db.command_permissions.set_command_permission(
                    guild_id=dashboard.guild.id,
                    command_name=command_name,
                    required_rank=rank_value,
                )
                message = f"✅ Command `{command_name}` assigned to Rank {rank_value} ({rank_obj.name})"
            else:
                # No valid selection made
                await interaction.response.send_message(
                    "❌ No valid selection made.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_message(message, ephemeral=True)

            # Invalidate cache and rebuild to show updated assignments
            await invalidate_and_rebuild(
                dashboard,
                "commands",
                dashboard.build_commands_mode,
                interaction,
            )

        except Exception as e:
            await handle_callback_error(
                interaction,
                e,
                "updating command permission",
                f"for {command_name}",
            )

    return callback


def create_channel_callback(dashboard: ConfigDashboard, option_key: str) -> Any:
    """Create a callback for channel selection."""

    async def callback(interaction: discord.Interaction) -> None:
        """Handle channel selection."""
        try:
            # Validate author
            if not await validate_author(
                interaction,
                dashboard.author,
                "❌ You are not authorized to modify this configuration.",
            ):
                return

            # Find channel select component
            custom_id = f"log_{option_key}"
            channel_select = dashboard.find_channel_select_component(custom_id)
            if not channel_select:
                await interaction.response.send_message(
                    "❌ Could not find channel selector",
                    ephemeral=True,
                )
                return

            # Resolve selected channel
            selected_channel = dashboard.resolve_channel_from_interaction(
                channel_select,
                interaction,
            )

            if selected_channel:
                await dashboard.update_channel_and_rebuild(
                    option_key,
                    selected_channel.id,
                    interaction,
                    f"✅ Channel set to {selected_channel.mention}",
                )
            else:
                await dashboard.update_channel_and_rebuild(
                    option_key,
                    None,
                    interaction,
                    "✅ Channel cleared",
                )
        except Exception as e:
            await handle_callback_error(
                interaction,
                e,
                "updating channel",
                f"for {option_key}",
            )

    return callback


def create_edit_rank_callback(
    dashboard: ConfigDashboard,
    rank_value: int,
    current_name: str,
    current_description: str | None,
) -> Any:
    """Create a callback for editing a rank."""

    async def callback(interaction: discord.Interaction) -> None:
        """Handle rank edit button click - opens modal."""
        if not await validate_author(
            interaction,
            dashboard.author,
            "❌ You are not authorized to edit ranks.",
        ):
            return

        # Create modal with pre-filled values
        modal = EditRankModal(
            dashboard.bot,
            dashboard.guild,
            dashboard,
            rank_value,
            current_name,
            current_description,
        )
        await interaction.response.send_modal(modal)

    return callback


def create_delete_rank_callback(
    dashboard: ConfigDashboard,
    rank_value: int,
    rank_name: str,
) -> Any:
    """Create a callback for deleting a rank."""

    async def callback(interaction: discord.Interaction) -> None:
        """Handle rank deletion."""
        if not await validate_author(
            interaction,
            dashboard.author,
            "❌ You are not authorized to delete ranks.",
        ):
            return

        try:
            # Check if rank exists
            existing = await dashboard.bot.db.permission_ranks.get_permission_rank(
                dashboard.guild.id,
                rank_value,
            )
            if not existing:
                await interaction.response.send_message(
                    f"❌ Rank {rank_value} does not exist.",
                    ephemeral=True,
                )
                return

            # Delete the rank
            await dashboard.bot.db.permission_ranks.delete_permission_rank(
                dashboard.guild.id,
                rank_value,
            )

            await interaction.response.defer()
            await interaction.followup.send(
                f"✅ Deleted rank **{rank_value}**: **{rank_name}**",
                ephemeral=True,
            )

            # Invalidate cache and rebuild to show updated ranks
            await invalidate_and_rebuild(
                dashboard,
                "ranks",
                dashboard.build_ranks_mode,
                interaction,
            )
        except Exception as e:
            await handle_callback_error(
                interaction,
                e,
                "deleting rank",
                f"{rank_value}",
            )

    return callback


def create_cancel_assignment_callback() -> Any:
    """Create callback for canceling role assignment."""

    async def cancel_assignment_callback(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "❌ Role assignment cancelled.",
            ephemeral=True,
        )

    return cancel_assignment_callback


def create_confirm_assignment_callback(
    dashboard: ConfigDashboard,
    rank_id: int,
    rank_db_id: int,
    selected_roles: list[discord.Role],
) -> Any:
    """Create callback for confirming role assignment."""

    async def confirm_assignment_callback(interaction: discord.Interaction) -> None:
        if not await validate_author(
            interaction,
            dashboard.author,
            "❌ You are not authorized to modify role assignments.",
        ):
            return

        if not selected_roles:
            await interaction.response.send_message(
                "❌ No roles selected.",
                ephemeral=True,
            )
            return

        try:
            assigned_count = 0
            existing_assignments = (
                await dashboard.bot.db.permission_assignments.get_assignments_by_guild(
                    dashboard.guild.id,
                )
            )

            for role in selected_roles:
                existing = any(
                    assignment.permission_rank_id == rank_db_id
                    and assignment.role_id == role.id
                    for assignment in existing_assignments
                )
                if not existing:
                    await (
                        dashboard.bot.db.permission_assignments.assign_permission_rank(
                            dashboard.guild.id,
                            rank_db_id,
                            role.id,
                        )
                    )
                    assigned_count += 1

            await interaction.response.send_message(
                f"✅ Successfully assigned {assigned_count} role(s) to Rank {rank_id}",
                ephemeral=True,
            )

            await invalidate_and_rebuild(
                dashboard,
                "roles",
                dashboard.build_roles_mode,
                interaction,
            )

        except Exception as e:
            await handle_callback_error(
                interaction,
                e,
                "assigning roles",
                f"to rank {rank_id}",
            )

    return confirm_assignment_callback


def create_role_selection_callback(
    dashboard: ConfigDashboard,
    rank_id: int,
    role_select: discord.ui.RoleSelect[discord.ui.LayoutView],
    assign_view: discord.ui.LayoutView,
    assign_container: discord.ui.Container[discord.ui.LayoutView],
    selected_roles: list[discord.Role],
    confirm_callback: Any,
    cancel_callback: Any,
) -> Any:
    """Create callback for role selection that updates the UI."""

    async def on_role_select(interaction: discord.Interaction) -> None:
        if not await validate_author(
            interaction,
            dashboard.author,
            "❌ You are not authorized to modify role assignments.",
        ):
            return

        selected_roles.clear()
        selected_roles.extend(role_select.values)

        try:
            dashboard.update_role_selection_ui(
                rank_id,
                selected_roles,
                role_select,
                assign_view,
                assign_container,
                confirm_callback,
                cancel_callback,
            )
            await interaction.response.edit_message(embed=None, view=assign_view)
        except Exception as e:
            await handle_callback_error(interaction, e, "updating role selection", "")

    return on_role_select
