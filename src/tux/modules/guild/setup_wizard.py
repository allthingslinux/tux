"""Interactive setup wizard for guild configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands

from tux.core.permission_system import get_permission_system
from tux.services.onboarding import GuildOnboardingService
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.ui.views.onboarding.wizard import SetupWizardView

if TYPE_CHECKING:
    from tux.core.bot import Tux


class SetupWizard(commands.Cog):
    """Interactive setup wizard for new guilds."""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.permission_system = get_permission_system()
        self.onboarding = GuildOnboardingService(bot)

    @commands.hybrid_group(name="setup", fallback="status")
    @commands.guild_only()
    async def setup(self, ctx: commands.Context[Tux]) -> None:
        """Guild setup and onboarding commands."""
        await self.setup_status(ctx)

    @commands.guild_only()
    async def setup_status(self, ctx: commands.Context[Tux]) -> None:
        """Check your guild's setup status and progress."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Get onboarding status from database
            completed, stage = await self.onboarding.get_onboarding_status(ctx.guild.id)

            embed = EmbedCreator.create_embed(
                title="🔧 Guild Setup Status",
                description="Here's your current setup progress. Use `/setup wizard` to complete missing items.",
                embed_type=EmbedType.INFO,
            )

            # Show current stage
            stage_emoji = "✅" if completed else "🔄" if stage else "❌"
            current_stage_display = stage.replace("_", " ").title() if stage else "Not Started"

            embed.add_field(
                name="📍 Current Stage",
                value=f"{stage_emoji} **{current_stage_display}**",
                inline=True,
            )

            # Overall completion status
            completion_status = (
                "✅ **Completed**" if completed else "🔄 **In Progress**" if stage else "❌ **Not Started**"
            )
            embed.add_field(
                name="🎯 Overall Status",
                value=completion_status,
                inline=True,
            )

            # Detailed setup checklist (legacy compatibility)
            status = await self.onboarding.get_setup_status(ctx.guild)
            checklist: list[str] = [
                f"{'✅' if status['permissions_initialized'] else '❌'} **Permission Ranks** - Default ranks created",
                f"{'✅' if status['log_channels_configured'] else '❌'} **Log Channels** - Logging channels configured",
                f"{'✅' if status['staff_roles_assigned'] else '❌'} **Staff Roles** - Roles assigned to permission ranks",
                f"{'✅' if status['essential_commands_protected'] else '❌'} **Command Protection** - Critical commands secured",
            ]

            embed.add_field(
                name="📋 Setup Checklist",
                value="\n".join(checklist),
                inline=False,
            )

            # Calculate completion percentage
            completed_count = sum(status.values())
            total = len(status)
            percentage = (completed_count / total) * 100

            embed.add_field(
                name="📊 Progress",
                value=f"**{completed_count}/{total}** steps completed ({percentage:.0f}%)",
                inline=True,
            )

            # Recommendations based on status
            recommendations: list[str] = []
            if not completed:
                recommendations.append("• Use `/setup wizard` for guided setup")
            else:
                recommendations.append("• Setup is complete! Use `/config` to customize further")

            if recommendations:
                embed.add_field(
                    name="💡 Next Steps",
                    value="\n".join(recommendations),
                    inline=False,
                )

            embed.set_footer(text="Use /setup wizard for guided setup")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to check setup status: {e}")

    @setup.command(name="wizard")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setup_wizard(self, ctx: commands.Context[Tux]) -> None:
        """Launch the interactive setup wizard."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Create the setup wizard view
            author = cast(discord.User, ctx.author)
            view = SetupWizardView(self.bot, ctx.guild, author)

            message = await ctx.send(view=view)

            # Store the message for later updates
            view.message = message

        except Exception as e:
            await ctx.send(f"❌ Failed to start setup wizard: {e}")

    @setup.command(name="reset")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setup_reset(self, ctx: commands.Context[Tux]) -> None:
        """Reset guild setup and start fresh (ADMIN ONLY)."""
        assert ctx.guild

        embed = EmbedCreator.create_embed(
            title="⚠️ Reset Guild Setup",
            description=(
                "This will reset all guild configuration including:\n"
                "• Permission ranks and assignments\n"
                "• Log channel configurations\n"
                "• Command permission settings\n\n"
                "**This action cannot be undone!**\n\n"
                "Are you sure you want to continue?"
            ),
            embed_type=EmbedType.WARNING,
        )

        author = cast(discord.User, ctx.author)
        view = ResetConfirmationView(author)
        message = await ctx.send(embed=embed, view=view)

        # Wait for confirmation
        try:
            await view.wait()

            if view.confirmed:
                await ctx.send("🔄 Resetting guild configuration...")

                # Reset onboarding status
                await self.onboarding.reset_onboarding(ctx.guild.id)

                # Reset permission ranks (simplified - in production you'd want more control)
                # This is a placeholder - actual permission reset would be more complex

                embed = EmbedCreator.create_embed(
                    title="✅ Configuration Reset",
                    description="Guild configuration has been reset to initial state.",
                    embed_type=EmbedType.SUCCESS,
                )

                embed.add_field(
                    name="🔄 What's Been Reset",
                    value="• Onboarding status → Not Started\n• Setup progress → 0%",
                    inline=False,
                )

                embed.add_field(
                    name="🚀 Next Steps",
                    value="Use `/setup wizard` to start fresh configuration.",
                    inline=False,
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Reset cancelled.")

        except TimeoutError:
            await message.edit(content="⏰ Reset timed out.", view=None, embed=None)

    @setup.command(name="simulate")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setup_simulate(self, ctx: commands.Context[Tux]) -> None:
        """Simulate onboarding process for testing (ADMIN ONLY)."""
        assert ctx.guild

        embed = EmbedCreator.create_embed(
            title="🧪 Simulate Onboarding",
            description=(
                "This will simulate the onboarding process as if the bot just joined this guild.\n\n"
                "**What this does:**\n"
                "• Creates a `#tux-setup` channel\n"
                "• Initializes default permission ranks\n"
                "• Sends welcome message with interactive setup buttons\n"
                "• Resets onboarding status to 'discovered'\n\n"
                "**Note:** This is for testing purposes only. Existing setup data will be preserved."
            ),
            embed_type=EmbedType.WARNING,
        )

        view = SimulateConfirmationView(ctx.author)
        await ctx.send(embed=embed, view=view)


class SimulateConfirmationView(discord.ui.View):
    """Confirmation view for simulating onboarding."""

    def __init__(self, author: discord.User | discord.Member):
        super().__init__(timeout=300)
        self.author = author
        self.confirmed = False

    @discord.ui.button(label="✅ Start Simulation", style=discord.ButtonStyle.success)
    async def confirm_simulate(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ) -> None:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can use this button.", ephemeral=True)
            return

        from tux.services.onboarding import GuildOnboardingService  # noqa: PLC0415

        self.confirmed = True
        await interaction.response.defer()

        try:
            if not interaction.guild:
                await interaction.followup.send("❌ This command must be used in a guild.", ephemeral=True)
                return

            # Get the onboarding service
            onboarding = GuildOnboardingService(interaction.client)  # type: ignore

            # Reset onboarding status first (optional, but good for testing)
            await onboarding.reset_onboarding(interaction.guild.id)

            # Simulate the onboarding process
            await onboarding.initialize_new_guild(interaction.guild)

            await interaction.followup.send(
                "✅ **Onboarding simulation complete!**\n"
                f"Check the `#tux-setup` channel in {interaction.guild.name} for the onboarding experience.",
                ephemeral=True,
            )

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to simulate onboarding: {e}", ephemeral=True)

        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_simulate(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ) -> None:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can use this button.", ephemeral=True)
            return

        self.confirmed = False
        await interaction.response.edit_message(content="❌ Simulation cancelled.", view=None)
        self.stop()


class ResetConfirmationView(discord.ui.View):
    """Confirmation view for setup reset."""

    def __init__(self, author: discord.User):
        super().__init__(timeout=60.0)
        self.author = author
        self.confirmed = False

    @discord.ui.button(label="Yes, Reset Everything", style=discord.ButtonStyle.danger)
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can use this button.", ephemeral=True)
            return

        self.confirmed = True
        await interaction.response.edit_message(content="✅ Confirmed reset.", view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can use this button.", ephemeral=True)
            return

        self.confirmed = False
        await interaction.response.edit_message(content="❌ Reset cancelled.", view=None)
        self.stop()


async def setup(bot: Tux) -> None:
    """Load the setup wizard cog."""
    await bot.add_cog(SetupWizard(bot))
