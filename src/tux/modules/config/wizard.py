"""Interactive setup wizard commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands

from tux.ui.embeds import EmbedCreator, EmbedType
from tux.ui.views.onboarding.wizard import SetupWizardView

if TYPE_CHECKING:
    from tux.core.bot import Tux


class ConfigWizard:
    """Wizard-related config commands."""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    async def wizard_command(self, ctx: commands.Context[Tux]) -> None:
        """Launch the interactive setup wizard."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Create the setup wizard view
            author = cast(discord.User, ctx.author)
            view = SetupWizardView(self.bot, ctx.guild, author)

            # Always start fresh - build the welcome step
            view.build_welcome_step()

            # Send the initial view
            await ctx.send(view=view)

            # Store the message for later updates (will be set after sending)
            view.message = None  # Will be updated when needed

        except Exception as e:
            await ctx.send(f"❌ Failed to start setup wizard: {e}")

    async def reset_command(self, ctx: commands.Context[Tux]) -> None:
        """Reset guild setup to allow re-running the wizard."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Confirm reset
            embed = EmbedCreator.create_embed(
                title="🔄 Reset Guild Setup",
                description=(
                    "**WARNING:** This will reset your guild's setup configuration.\n\n"
                    "This action will:\n"
                    "• Clear all setup progress\n"
                    "• Allow re-running the setup wizard\n"
                    "• **Keep existing permissions and roles intact**\n\n"
                    "Are you sure you want to continue?"
                ),
                embed_type=EmbedType.WARNING,
                custom_color=discord.Color.orange(),
            )

            # Create confirmation buttons
            view = ResetConfirmationView()
            await ctx.send(embed=embed, view=view)

            # Store context for callback
            view.ctx = ctx
            view.bot = self.bot

        except Exception as e:
            await ctx.send(f"❌ Failed to reset setup: {e}")


class ResetConfirmationView(discord.ui.View):
    """Confirmation view for setup reset."""

    def __init__(self) -> None:
        super().__init__(timeout=300.0)  # 5 minutes
        self.ctx: commands.Context[Tux] | None = None
        self.bot: Tux | None = None

    @discord.ui.button(label="Yes, Reset Setup", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        """Confirm and perform the setup reset."""
        if not self.ctx or not self.bot:
            await interaction.response.send_message("❌ Reset failed: Context not available.", ephemeral=True)
            return

        # Ensure author is available
        assert self.ctx.author is not None

        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Only the command author can reset setup.", ephemeral=True)
            return

        try:
            # Ensure we have valid context
            assert self.ctx.guild is not None

            # Perform the reset (no onboarding records to clean up)

            # Update onboarding stage
            await self.bot.db.guild_config.update_onboarding_stage(self.ctx.guild.id, "not_started")

            embed = EmbedCreator.create_embed(
                title="✅ Setup Reset Complete",
                description="Guild setup has been reset. You can now run `/config wizard` again.",
                embed_type=EmbedType.SUCCESS,
            )

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to reset setup: {e}", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        """Cancel the reset operation."""
        # Ensure we have valid context
        if not self.ctx or not self.ctx.author:
            await interaction.response.send_message("❌ Context not available.", ephemeral=True)
            return

        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Only the command author can cancel.", ephemeral=True)
            return

        embed = EmbedCreator.create_embed(
            title="❌ Reset Cancelled",
            description="Setup reset has been cancelled. No changes were made.",
            embed_type=EmbedType.INFO,
        )

        await interaction.response.edit_message(embed=embed, view=None)
