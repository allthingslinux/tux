"""Guild onboarding service for automated setup and configuration guidance."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, cast

import discord
from loguru import logger

from tux.core.permission_system import get_permission_system
from tux.database.models.enums import OnboardingStage
from tux.ui.embeds import EmbedCreator, EmbedType

from .utils import get_channel_permissions_overwrites, send_fallback_welcome_message

if TYPE_CHECKING:
    from tux.core.bot import Tux


class GuildOnboardingService:
    """Service for handling new guild setup and configuration guidance.

    This service provides:
    - Automated permission rank initialization for new guilds
    - Interactive setup wizard for essential configuration
    - Smart channel discovery for logging setup
    - Setup status tracking and verification
    - Helpful guidance for server administrators
    """

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.permission_system = get_permission_system()

    async def initialize_new_guild(self, guild: discord.Guild) -> None:
        """Initialize a new guild with basic permission structure and create onboarding channel."""
        try:
            with self.bot.sentry_manager.start_transaction(
                "guild.onboarding",
                f"Setting up guild {guild.id}",
            ) as transaction:
                transaction.set_tag("guild_id", str(guild.id))
                transaction.set_tag("guild_name", guild.name)

                # Initialize default permission ranks
                await self._initialize_permission_ranks(guild)

                # Create dedicated onboarding channel
                onboarding_channel = await self._create_onboarding_channel(guild)

                # Set onboarding stage to discovered (user aware of bot)
                await self.bot.db.guild_config.update_onboarding_stage(guild.id, OnboardingStage.DISCOVERED)

                # Send welcome message to the new onboarding channel
                if onboarding_channel:
                    await self._send_onboarding_embed(onboarding_channel)
                else:
                    # Fallback to system channel if we couldn't create the onboarding channel
                    await send_fallback_welcome_message(guild, self.bot)

                transaction.set_tag("onboarding_stage", OnboardingStage.DISCOVERED)
                transaction.set_tag("onboarding_channel_created", onboarding_channel is not None)
                logger.info(f"✅ Completed initial onboarding for guild {guild.id} ({guild.name})")

        except Exception as e:
            logger.error(f"❌ Failed to initialize guild {guild.id}: {e}")
            if self.bot.sentry_manager.is_initialized:
                self.bot.sentry_manager.capture_exception(e)
            # Don't re-raise - we don't want to break guild join

    async def _initialize_permission_ranks(self, guild: discord.Guild) -> None:
        """Initialize default permission ranks for a new guild."""
        try:
            await self.permission_system.initialize_guild(guild.id)
            logger.info(f"Initialized default permission ranks for guild {guild.id}")
        except Exception as e:
            logger.warning(f"Failed to initialize permission ranks for guild {guild.id}: {e}")
            # Continue with onboarding even if this fails

    async def _create_onboarding_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Create a dedicated onboarding channel for the guild."""
        try:
            # Check if bot has permission to create channels
            if not guild.me.guild_permissions.manage_channels:
                logger.warning(f"No permission to create channels in guild {guild.id}")
                return None

            # Create the onboarding channel
            overwrites = cast(
                Mapping[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite],
                get_channel_permissions_overwrites(guild),
            )

            channel = await guild.create_text_channel(
                name="tux-setup",
                topic="🚀 Complete your Tux bot setup here!",
                overwrites=overwrites,
                reason="Creating onboarding channel for Tux bot setup",
            )

        except discord.Forbidden:
            logger.warning(f"Forbidden to create channel in guild {guild.id}")
            return None
        except Exception as e:
            logger.error(f"Failed to create onboarding channel for guild {guild.id}: {e}")
            return None
        else:
            # Only executed if no exception occurred
            logger.info(f"Created onboarding channel {channel.id} in guild {guild.id}")
            return channel

    async def _send_onboarding_embed(self, channel: discord.TextChannel) -> None:
        """Send a comprehensive onboarding embed to the dedicated channel."""
        try:
            embed = EmbedCreator.create_embed(
                title="🎉 Welcome to Tux!",
                description=(
                    f"Thanks for adding **Tux** to **{channel.guild.name}**! 🎯\n\n"
                    "I'm your friendly Discord moderation bot, here to help keep your server safe and organized.\n\n"
                    "**🚀 Let's get you set up in just a few minutes!**"
                ),
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.blue(),
            )

            embed.add_field(
                name="📋 What We'll Set Up",
                value=(
                    "• **Permission System** - Custom roles and access levels\n"
                    "• **Moderation Tools** - Ban, kick, timeout, and jail commands\n"
                    "• **Log Channels** - Track all moderation actions\n"
                    "• **Staff Roles** - Assign moderator permissions\n"
                    "• **Command Security** - Protect sensitive features"
                ),
                inline=False,
            )

            embed.add_field(
                name="🎯 Quick Start",
                value=(
                    "Click the button below to launch the **interactive setup wizard**!\n\n"
                    "⏱️ **Time estimate:** 3-5 minutes\n"
                    "🛡️ **Completely safe:** Nothing breaks if you stop midway\n"
                    "🔄 **Resume anytime:** Pick up where you left off"
                ),
                inline=False,
            )

            embed.add_field(
                name="💡 Already Done?",
                value="If you've already completed setup, this channel will be cleaned up automatically.",
                inline=False,
            )

            embed.set_footer(text="Ready to get started? Click the button below!")

            # Create a view with the setup button
            from tux.ui.views.onboarding.start_view import OnboardingStartView  # noqa: PLC0415

            view = OnboardingStartView(self.bot, channel.guild)

            message = await channel.send(embed=embed, view=view)

            # Pin the message so it can be updated as a progress dashboard
            with suppress(Exception):
                await message.pin()

            logger.info(f"Sent onboarding embed to channel {channel.id} in guild {channel.guild.id}")

        except Exception as e:
            logger.error(f"Failed to send onboarding embed to channel {channel.id}: {e}")

    async def update_onboarding_stage(self, guild_id: int, stage: OnboardingStage) -> None:
        """Update the onboarding stage for a guild."""
        try:
            await self.bot.db.guild_config.update_onboarding_stage(guild_id, stage.value)
            logger.info(f"Updated onboarding stage for guild {guild_id} to {stage.value}")

            # Mark as completed if they've reached the final stage
            if stage == OnboardingStage.COMPLETED:
                await self.mark_onboarding_completed(guild_id)

        except Exception as e:
            logger.error(f"Failed to update onboarding stage for guild {guild_id}: {e}")

    async def mark_onboarding_completed(self, guild_id: int) -> None:
        """Mark onboarding as completed for a guild."""
        try:
            await self.bot.db.guild_config.mark_onboarding_completed(guild_id)
            logger.info(f"Marked onboarding as completed for guild {guild_id}")
        except Exception as e:
            logger.error(f"Failed to mark onboarding completed for guild {guild_id}: {e}")

    async def reset_onboarding(self, guild_id: int) -> None:
        """Reset onboarding status for a guild."""
        try:
            await self.bot.db.guild_config.reset_onboarding(guild_id)
            logger.info(f"Reset onboarding status for guild {guild_id}")
        except Exception as e:
            logger.error(f"Failed to reset onboarding for guild {guild_id}: {e}")

    async def get_onboarding_status(self, guild_id: int) -> tuple[bool, str | None]:
        """Get onboarding status for a guild. Returns (completed, stage)."""
        try:
            return await self.bot.db.guild_config.get_onboarding_status(guild_id)
        except Exception as e:
            logger.error(f"Failed to get onboarding status for guild {guild_id}: {e}")
            return False, None

    async def is_onboarding_completed(self, guild_id: int) -> bool:
        """Check if onboarding is completed for a guild."""
        completed, _ = await self.get_onboarding_status(guild_id)
        return completed

    async def get_setup_status(self, guild: discord.Guild) -> dict[str, bool]:
        """Get the current setup status for a guild."""
        status = {
            "permissions_initialized": False,
            "log_channels_configured": False,
            "staff_roles_assigned": False,
            "essential_commands_protected": False,
        }

        try:
            # Check if permission ranks exist
            ranks = await self.permission_system.get_guild_permission_ranks(guild.id)
            status["permissions_initialized"] = len(ranks) > 0

            # Check if any log channels are configured
            config = await self.bot.db.guild_config.get_config_by_guild_id(guild.id)

            if config:
                log_channels = [
                    config.mod_log_id,
                    config.audit_log_id,
                    config.join_log_id,
                    config.private_log_id,
                    config.report_log_id,
                    config.dev_log_id,
                ]
                status["log_channels_configured"] = any(channel_id is not None for channel_id in log_channels)
            else:
                status["log_channels_configured"] = False

            # Check if any roles are assigned to permission ranks
            assignments = await self.permission_system.get_guild_assignments(guild.id)
            status["staff_roles_assigned"] = len(assignments) > 0

            # Check if critical commands have permission requirements
            critical_commands = ["ban", "kick", "timeout", "jail", "config"]
            command_permissions = await self.bot.db.command_permissions.get_all_command_permissions(guild.id)
            protected_commands = {cmd.command_name for cmd in command_permissions}
            status["essential_commands_protected"] = any(cmd in protected_commands for cmd in critical_commands)

        except Exception as e:
            logger.error(f"Failed to get setup status for guild {guild.id}: {e}")

        return status

    async def update_progress_channel(self, guild: discord.Guild) -> None:
        """Update the onboarding channel with current progress status."""
        try:
            # Look for a channel named "tux-setup"
            onboarding_channel = discord.utils.get(guild.channels, name="tux-setup")
            if not onboarding_channel or not isinstance(onboarding_channel, discord.TextChannel):
                return  # Channel doesn't exist or isn't accessible

            # Get current status
            completed, _stage = await self.get_onboarding_status(guild.id)
            setup_status = await self.get_setup_status(guild)

            if completed:
                # Show completion status
                embed = EmbedCreator.create_embed(
                    title="🎉 Setup Complete!",
                    description=(
                        f"**Congratulations!** {guild.name} is fully configured with Tux.\n\n"
                        "Your server is ready to use all features safely and effectively."
                    ),
                    embed_type=EmbedType.SUCCESS,
                    custom_color=discord.Color.green(),
                )

                embed.add_field(
                    name="✅ Configuration Summary",
                    value=(
                        "• **Permission System**: Active\n"
                        "• **Moderation Tools**: Ready\n"
                        "• **Log Channels**: Configured\n"
                        "• **Staff Roles**: Assigned\n"
                        "• **Command Security**: Enabled"
                    ),
                    inline=False,
                )

            else:
                # Show progress status
                completed_count = sum(setup_status.values())
                total_count = len(setup_status)
                percentage = int((completed_count / total_count) * 100)

                embed = EmbedCreator.create_embed(
                    title="🚧 Tux Setup In Progress",
                    description=(
                        f"**{guild.name}** is setting up Tux for optimal server management.\n\n"
                        f"**Progress: {percentage}%** ({completed_count}/{total_count} steps complete)"
                    ),
                    embed_type=EmbedType.INFO,
                    custom_color=discord.Color.blue(),
                )

                # Progress checklist
                checklist_items = [
                    (setup_status["permissions_initialized"], "Permission Ranks"),
                    (setup_status["log_channels_configured"], "Log Channels"),
                    (setup_status["staff_roles_assigned"], "Staff Roles"),
                    (setup_status["essential_commands_protected"], "Command Protection"),
                ]
                checklist: list[str] = [f"{'✅' if completed else '❌'} {name}" for completed, name in checklist_items]

                embed.add_field(
                    name="📋 Setup Checklist",
                    value="\n".join(checklist),
                    inline=False,
                )

                # Next steps
                if percentage < 100:
                    embed.add_field(
                        name="🎯 Next Steps",
                        value="Continue the setup wizard to complete configuration!",
                        inline=False,
                    )

            embed.set_footer(text="Use /setup status for detailed progress")

            # Try to update pinned message, otherwise send new one
            try:
                pinned_messages = await onboarding_channel.pins()
                if pinned_messages:
                    await pinned_messages[0].edit(embed=embed)
                else:
                    message = await onboarding_channel.send(embed=embed)
                    await message.pin()
            except Exception:
                # If pinning fails, just send the message
                await onboarding_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to update progress channel for guild {guild.id}: {e}")
