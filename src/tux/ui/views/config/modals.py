"""
Modal dialogs for config dashboard.

Provides reusable modal components for rank management and other
configuration operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

if TYPE_CHECKING:
    from tux.core.bot import Tux


class EditRankModal(discord.ui.Modal):
    """Modal for editing an existing permission rank."""

    def __init__(
        self,
        bot: Tux,
        guild: discord.Guild,
        dashboard: Any,
        rank_value: int,
        current_name: str,
        current_description: str | None,
    ) -> None:
        super().__init__(title=f"Edit Rank {rank_value}")
        self.bot = bot
        self.guild = guild
        self.dashboard = dashboard
        self.rank_value = rank_value

        # Create text inputs with pre-filled values using default parameter
        self.rank_name: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
            label="Rank Name",
            placeholder="e.g., Elite Moderator, Super Admin",
            required=True,
            max_length=100,
            min_length=1,
            default=current_name,
        )

        self.rank_description: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
            label="Description",
            placeholder="Describe this rank's purpose and responsibilities",
            required=False,
            max_length=500,
            style=discord.TextStyle.paragraph,
            default=current_description or "",
        )

        # Add the inputs to the modal
        self.add_item(self.rank_name)
        self.add_item(self.rank_description)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        try:
            # Check if rank exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(self.guild.id, self.rank_value)
            if not existing:
                await interaction.response.send_message(f"❌ Rank {self.rank_value} does not exist.", ephemeral=True)
                return

            # Check if name already exists (but allow keeping the same name)
            all_ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(self.guild.id)
            if any(
                rank.name.lower() == self.rank_name.value.lower() and rank.rank != self.rank_value for rank in all_ranks
            ):
                await interaction.response.send_message(
                    f"❌ A rank with the name **{self.rank_name.value}** already exists.",
                    ephemeral=True,
                )
                return

            # Update the rank
            description = self.rank_description.value or None
            updated = await self.bot.db.permission_ranks.update_permission_rank(
                guild_id=self.guild.id,
                rank=self.rank_value,
                name=self.rank_name.value,
                description=description,
            )

            if not updated:
                await interaction.response.send_message(f"❌ Failed to update rank {self.rank_value}.", ephemeral=True)
                return

            await interaction.response.send_message(
                f"✅ Updated rank **{self.rank_value}**: **{self.rank_name.value}**",
                ephemeral=True,
            )

            # Invalidate cache and rebuild to show updated rank
            self.dashboard.invalidate_cache()
            self.dashboard.current_mode = "ranks"
            await self.dashboard.build_ranks_mode()
            if interaction.message:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    view=self.dashboard,
                )
        except Exception as e:
            logger.error(f"Error updating rank: {e}", exc_info=True)
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(f"❌ Error updating rank: {e}", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"❌ Error updating rank: {e}",
                        ephemeral=True,
                        delete_after=5,
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")


class CreateRankModal(discord.ui.Modal):
    """Modal for creating a new permission rank."""

    def __init__(self, bot: Tux, guild: discord.Guild, dashboard: Any) -> None:
        super().__init__(title="Create Permission Rank")
        self.bot = bot
        self.guild = guild
        self.dashboard = dashboard

    rank_number: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Rank Number",
        placeholder="Enter rank number (8-10)",
        required=True,
        max_length=3,
        min_length=1,
    )

    rank_name: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Rank Name",
        placeholder="e.g., Elite Moderator, Super Admin",
        required=True,
        max_length=100,
        min_length=1,
    )

    rank_description: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Description",
        placeholder="Describe this rank's purpose and responsibilities",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        try:
            # Parse rank number
            try:
                rank_value = int(self.rank_number.value)
            except ValueError:
                await interaction.response.send_message("❌ Rank number must be a valid integer.", ephemeral=True)
                return

            # Validate rank range
            if rank_value < 8 or rank_value > 10:
                await interaction.response.send_message(
                    "❌ Rank number must be between 8 and 10.\n\nRanks 0-7 are reserved for default ranks.",
                    ephemeral=True,
                )
                return

            # Check if rank already exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(self.guild.id, rank_value)
            if existing:
                await interaction.response.send_message(
                    f"❌ Rank {rank_value} already exists: **{existing.name}**",
                    ephemeral=True,
                )
                return

            # Check if name already exists
            all_ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(self.guild.id)
            if any(rank.name.lower() == self.rank_name.value.lower() for rank in all_ranks):
                await interaction.response.send_message(
                    f"❌ A rank with the name **{self.rank_name.value}** already exists.",
                    ephemeral=True,
                )
                return

            # Create the rank
            description = self.rank_description.value or None
            await self.bot.db.permission_ranks.create_permission_rank(
                guild_id=self.guild.id,
                rank=rank_value,
                name=self.rank_name.value,
                description=description,
            )

            await interaction.response.send_message(
                f"✅ Created rank **{rank_value}**: **{self.rank_name.value}**",
                ephemeral=True,
            )

            # Invalidate cache and rebuild to show new rank
            self.dashboard.invalidate_cache()
            self.dashboard.current_mode = "ranks"
            await self.dashboard.build_ranks_mode()
            if interaction.message:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    view=self.dashboard,
                )
        except Exception as e:
            logger.error(f"Error creating rank: {e}", exc_info=True)
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(f"❌ Error creating rank: {e}", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"❌ Error creating rank: {e}",
                        ephemeral=True,
                        delete_after=5,
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
