"""Refactored Clean Components V2 setup wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import discord
from loguru import logger

from tux.core.permission_system import get_permission_system

from .callbacks import (
    handle_audit_log_channel_select,
    handle_dev_log_channel_select,
    handle_jail_channel_select,
    handle_jail_role_select,
    handle_join_log_channel_select,
    handle_mod_log_channel_select,
    handle_permission_rank_role_select,
    handle_private_log_channel_select,
    handle_report_log_channel_select,
)
from .steps import (
    ChannelsStep,
    CompletionStep,
    PermissionsStep,
    RolesStep,
    WelcomeStep,
)

if TYPE_CHECKING:
    from tux.core.bot import Tux


class SetupWizardView(discord.ui.LayoutView):
    """Clean setup wizard using Components V2."""

    def __init__(self, bot: Tux, guild: discord.Guild, author: discord.User) -> None:
        """Initialize the setup wizard view.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        guild : discord.Guild
            The guild being set up.
        author : discord.User
            The user initiating the setup.
        """
        super().__init__(timeout=900.0)  # 15 minute timeout
        self.bot = bot
        self.guild = guild
        self.author = author
        self.permission_system = get_permission_system()

        logger.info(f"Creating SetupWizardView for guild {guild.id} with author {author}")

        # Setup state
        self.current_step = 0
        self.setup_data: dict[str, bool] = {
            "permissions_initialized": False,
            "log_channels_set": False,
            "roles_assigned": False,
        }

        # Selected channels and roles
        self.selected_mod_log_channel: discord.TextChannel | None = None
        self.selected_audit_log_channel: discord.TextChannel | None = None
        self.selected_join_log_channel: discord.TextChannel | None = None
        self.selected_private_log_channel: discord.TextChannel | None = None
        self.selected_report_log_channel: discord.TextChannel | None = None
        self.selected_dev_log_channel: discord.TextChannel | None = None
        self.selected_jail_channel: discord.TextChannel | None = None
        self.selected_jail_role: discord.Role | None = None
        self.selected_permission_roles: dict[int, list[discord.Role]] = {}

        # UI components that will be set by steps
        self.status_text: discord.ui.TextDisplay[Self] | None = None
        self.continue_button: discord.ui.Button[Self] | None = None
        self.selected_channels_text: discord.ui.TextDisplay[Self] | None = None
        self.selected_roles_text: discord.ui.TextDisplay[Self] | None = None

        # Discord message reference for updates
        self.message: discord.Message | None = None

        # Initialize step builders
        self.steps = {
            0: WelcomeStep(self),
            1: PermissionsStep(self),
            2: ChannelsStep(self),
            3: RolesStep(self),
            4: CompletionStep(self),
        }

        logger.info(f"SetupWizardView initialized with {len(self.children)} children")

    def build_welcome_step(self) -> None:
        """Build the welcome step."""
        self.current_step = 0
        self.steps[0].build()

    def build_permissions_step(self) -> None:
        """Build the permissions initialization step."""
        self.current_step = 1
        self.steps[1].build()

    def build_channels_step(self) -> None:
        """Build the log channels selection step."""
        self.current_step = 2
        self.steps[2].build()

    def build_roles_step(self) -> None:
        """Build the staff roles assignment step."""
        self.current_step = 3
        self.steps[3].build()

    def _build_completion_step(self) -> None:
        """Build the completion step."""
        self.current_step = 4
        self.steps[4].build()

    # Callback methods that delegate to the callback handlers
    async def on_mod_log_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle moderation log channel selection."""
        await handle_mod_log_channel_select(interaction, self)

    async def on_audit_log_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle audit log channel selection."""
        await handle_audit_log_channel_select(interaction, self)

    async def on_join_log_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle join log channel selection."""
        await handle_join_log_channel_select(interaction, self)

    async def on_private_log_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle private log channel selection."""
        await handle_private_log_channel_select(interaction, self)

    async def on_report_log_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle report log channel selection."""
        await handle_report_log_channel_select(interaction, self)

    async def on_dev_log_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle dev log channel selection."""
        await handle_dev_log_channel_select(interaction, self)

    async def on_jail_channel_select(self, interaction: discord.Interaction) -> None:
        """Handle jail channel selection."""
        await handle_jail_channel_select(interaction, self)

    async def on_jail_role_select(self, interaction: discord.Interaction) -> None:
        """Handle jail role selection."""
        await handle_jail_role_select(interaction, self)

    async def on_permission_rank_role_select(
        self,
        interaction: discord.Interaction,
        rank: int,
        roles: list[discord.Role],
    ) -> None:
        """Handle permission rank role selection."""
        await handle_permission_rank_role_select(interaction, self, rank, roles)

    async def update_channels_display(self) -> None:
        """Update the channels display text."""
        selected_channels: list[str] = []

        if self.selected_mod_log_channel:
            selected_channels.append(f"**Moderation:** {self.selected_mod_log_channel.mention}")
        if self.selected_audit_log_channel:
            selected_channels.append(f"**Audit:** {self.selected_audit_log_channel.mention}")
        if self.selected_join_log_channel:
            selected_channels.append(f"**Join/Leave:** {self.selected_join_log_channel.mention}")
        if self.selected_private_log_channel:
            selected_channels.append(f"**Private:** {self.selected_private_log_channel.mention}")
        if self.selected_report_log_channel:
            selected_channels.append(f"**Report:** {self.selected_report_log_channel.mention}")
        if self.selected_dev_log_channel:
            selected_channels.append(f"**Dev:** {self.selected_dev_log_channel.mention}")
        if self.selected_jail_channel:
            selected_channels.append(f"**Jail:** {self.selected_jail_channel.mention}")

        if self.selected_channels_text:
            display_text = "\n".join(selected_channels) if selected_channels else "No channels selected yet."
            self.selected_channels_text.content = display_text

    def update_roles_display(self) -> None:
        """Update the roles display text."""
        # Build display text from selected permission roles
        selected_roles: list[str] = []

        # Default rank names
        rank_names = {
            1: "Trusted",
            2: "Junior Moderator",
            3: "Moderator",
            4: "Senior Moderator",
            5: "Administrator",
            6: "Head Administrator",
            7: "Server Owner",
        }

        for rank in sorted(self.selected_permission_roles.keys()):
            if roles := self.selected_permission_roles[rank]:
                role_mentions = [role.mention for role in roles]
                rank_name = rank_names.get(rank, f"Rank {rank}")
                selected_roles.append(f"**{rank_name}:** {', '.join(role_mentions)}")

        # Add jail role if selected
        if self.selected_jail_role:
            selected_roles.append(f"**Jail Role:** {self.selected_jail_role.mention}")

        if self.selected_roles_text:
            display_text = "\n".join(selected_roles) if selected_roles else "No roles assigned yet."
            self.selected_roles_text.content = display_text

    async def initialize_permissions(self, interaction: discord.Interaction) -> None:
        """Initialize the permission system."""
        try:
            logger.info(f"Updating status to 'Initializing permission ranks...' for guild {self.guild.id}")
            # Update status
            if self.status_text:
                self.status_text.content = "Initializing permission ranks..."
            await interaction.response.edit_message(view=self)
            logger.info(f"Successfully updated message with initializing status for guild {self.guild.id}")

            logger.info(f"Calling initialize_new_guild for guild {self.guild.id}")
            # Initialize permissions
            await self.permission_system.initialize_guild(self.guild.id)
            self.setup_data["permissions_initialized"] = True
            logger.info(f"Successfully initialized permissions for guild {self.guild.id}")

            logger.info(f"Updating status to success and enabling continue button for guild {self.guild.id}")
            # Update status and enable continue button
            if self.status_text:
                self.status_text.content = "✅ Permission system initialized successfully!"
            if self.continue_button:
                self.continue_button.disabled = False
            await interaction.edit_original_response(view=self)
            logger.info(f"Successfully updated message with success status for guild {self.guild.id}")

            logger.info(f"Initialized permission ranks for guild {self.guild.id}")

        except Exception as e:
            logger.error(f"Failed to initialize permissions for guild {self.guild.id}: {e}")
            if self.status_text:
                self.status_text.content = f"❌ Failed to initialize permissions: {e}"
            try:
                await interaction.edit_original_response(view=self)
            except Exception as followup_error:
                logger.error(f"Failed to update message after error for guild {self.guild.id}: {followup_error}")
                await interaction.followup.send(f"❌ Failed to initialize permissions: {e}", ephemeral=True)

    async def complete_setup(self, interaction: discord.Interaction) -> None:
        """Complete the setup process."""
        try:
            # Save log channels to database
            await self._save_log_channels()

            # Update onboarding stage
            await self.bot.db.guild_config.mark_onboarding_completed(self.guild.id)

            # Build completion step
            self._build_completion_step()
            await interaction.response.edit_message(view=self)

            logger.info(f"Completed onboarding for guild {self.guild.id}")

        except Exception as e:
            logger.error(f"Failed to complete setup: {e}")
            await interaction.response.send_message(f"❌ Failed to complete setup: {e}", ephemeral=True)

    async def _save_log_channels(self) -> None:
        """Save selected log channels and roles to the database."""
        config_updates = {}

        # Log channels
        if self.selected_mod_log_channel:
            config_updates["mod_log_id"] = self.selected_mod_log_channel.id
        if self.selected_audit_log_channel:
            config_updates["audit_log_id"] = self.selected_audit_log_channel.id
        if self.selected_join_log_channel:
            config_updates["join_log_id"] = self.selected_join_log_channel.id
        if self.selected_private_log_channel:
            config_updates["private_log_id"] = self.selected_private_log_channel.id
        if self.selected_report_log_channel:
            config_updates["report_log_id"] = self.selected_report_log_channel.id
        if self.selected_dev_log_channel:
            config_updates["dev_log_id"] = self.selected_dev_log_channel.id
        if self.selected_jail_channel:
            config_updates["jail_channel_id"] = self.selected_jail_channel.id
        if self.selected_jail_role:
            config_updates["jail_role_id"] = self.selected_jail_role.id

        if config_updates:
            config_controller = self.bot.db.guild_config
            await config_controller.update_config(self.guild.id, **config_updates)
            logger.info(f"Saved log channels and roles for guild {self.guild.id}: {config_updates}")

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        logger.info(f"Setup wizard timed out for guild {self.guild.id}")

        self.stop()
