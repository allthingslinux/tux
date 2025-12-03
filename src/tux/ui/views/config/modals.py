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

        self.rank_description: discord.ui.TextInput[discord.ui.Modal] = (
            discord.ui.TextInput(
                label="Description",
                placeholder="Describe this rank's purpose and responsibilities",
                required=False,
                max_length=500,
                style=discord.TextStyle.paragraph,
                default=current_description or "",
            )
        )

        # Add the inputs to the modal
        self.add_item(self.rank_name)
        self.add_item(self.rank_description)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        try:
            # Check if rank exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(
                self.guild.id,
                self.rank_value,
            )
            if not existing:
                await interaction.response.send_message(
                    f"❌ Rank {self.rank_value} does not exist.",
                    ephemeral=True,
                )
                return

            # Check if name already exists (but allow keeping the same name)
            all_ranks = (
                await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                    self.guild.id,
                )
            )
            if any(
                rank.name.lower() == self.rank_name.value.lower()
                and rank.rank != self.rank_value
                for rank in all_ranks
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
                await interaction.response.send_message(
                    f"❌ Failed to update rank {self.rank_value}.",
                    ephemeral=True,
                )
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
                    await interaction.followup.send(
                        f"❌ Error updating rank: {e}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"❌ Error updating rank: {e}",
                        ephemeral=True,
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")


class CreateRankModal(discord.ui.Modal):
    """Modal for creating a new permission rank."""

    def __init__(
        self,
        bot: Tux,
        guild: discord.Guild,
        dashboard: Any,
        available_ranks: list[int] | None = None,
    ) -> None:
        super().__init__(title="Create Permission Rank")
        self.bot = bot
        self.guild = guild
        self.dashboard = dashboard

        # Create select with only available ranks
        if available_ranks is None:
            available_ranks = list(range(11))  # Fallback to all ranks

        options = [
            discord.SelectOption(
                label=f"Rank {rank_num}",
                description="Default Rank" if rank_num < 8 else "Custom Rank",
                value=str(rank_num),
            )
            for rank_num in available_ranks
        ]

        # basedpyright strict mode flags incomplete discord.py type annotations for Components V2
        self.rank_number = discord.ui.Label(  # type: ignore[reportUnknownVariableType]
            text="Rank Number",
            description="Select the rank number to create",
            component=discord.ui.Select(  # type: ignore[reportUnknownArgumentType]
                custom_id="rank_number",
                placeholder="Select available rank number",
                min_values=1,
                max_values=1,
                options=options,
            ),
        )
        self.add_item(self.rank_number)  # type: ignore[reportUnknownArgumentType]

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
            # Tell the type checker what our components are...
            # basedpyright strict mode needs help with discord.py Components V2 types
            assert isinstance(self.rank_number.component, discord.ui.Select)  # type: ignore[reportUnknownMemberType]

            # Get rank number from select
            try:
                rank_value = int(self.rank_number.component.values[0])  # type: ignore[reportUnknownMemberType]
            except (ValueError, IndexError):
                await interaction.response.send_message(
                    "❌ Invalid rank selection.",
                    ephemeral=True,
                )
                return

            # Double-check availability (in case of race conditions or UI inconsistencies)
            existing_ranks = (
                await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                    self.guild.id,
                )
            )
            existing_rank_values = {rank.rank for rank in existing_ranks}

            # Allow creating ranks 0-7 if they're missing, or ranks 8-10
            default_ranks = set(range(8))  # 0-7
            custom_ranks = set(range(8, 11))  # 8-10
            missing_default_ranks = default_ranks - existing_rank_values
            available_ranks = missing_default_ranks | custom_ranks

            if rank_value not in available_ranks:
                await interaction.response.send_message(
                    f"❌ Rank {rank_value} is no longer available to create.",
                    ephemeral=True,
                )
                return

            # Check if name already exists
            all_ranks = (
                await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                    self.guild.id,
                )
            )
            if any(
                rank.name.lower() == self.rank_name.value.lower() for rank in all_ranks
            ):
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
                    await interaction.followup.send(
                        f"❌ Error creating rank: {e}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"❌ Error creating rank: {e}",
                        ephemeral=True,
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
