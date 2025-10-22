"""Button components for the onboarding wizard."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import discord
from loguru import logger

from .base import WizardComponent

if TYPE_CHECKING:
    from ..wizard import SetupWizardView


class StartButton(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Start setup button."""

    def __init__(self) -> None:
        """Initialize the start button."""
        super().__init__(
            label="Start Setup",
            style=discord.ButtonStyle.primary,
            emoji="🚀",
            id=109,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle start button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"🚀 START BUTTON CLICKED! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            logger.info(f"Starting permissions initialization for guild {wizard_view.guild.id}")
            wizard_view.current_step = 1
            wizard_view.build_permissions_step()
            await wizard_view.initialize_permissions(interaction)
            logger.info(f"Successfully started permissions initialization for guild {wizard_view.guild.id}")
        except Exception as e:
            logger.error(f"Failed to start permissions initialization for guild {wizard_view.guild.id}: {e}")
            await interaction.response.send_message(f"❌ Failed to start setup: {e}", ephemeral=True)


class CancelButton(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Cancel setup button."""

    def __init__(self) -> None:
        """Initialize the cancel button."""
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji="❌",
            id=110,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle cancel button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        await interaction.response.send_message("❌ Setup wizard cancelled.", ephemeral=True)
        wizard_view.stop()


class ContinueButton(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Continue button for the permissions step."""

    def __init__(self) -> None:
        """Initialize the continue button."""
        super().__init__(
            label="Continue",
            style=discord.ButtonStyle.primary,
            disabled=True,
            id=206,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle continue button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"🔄 CONTINUE BUTTON CLICKED! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            logger.info(f"Moving to channels step for guild {wizard_view.guild.id}")
            wizard_view.current_step = 2
            wizard_view.build_channels_step()
            await interaction.response.edit_message(view=cast("SetupWizardView", wizard_view))
            logger.info(f"Successfully moved to channels step for guild {wizard_view.guild.id}")
        except Exception as e:
            logger.error(f"Failed to move to channels step for guild {wizard_view.guild.id}: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to continue: {e}", ephemeral=True)


class BackButtonPermissions(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Back button for the permissions step."""

    def __init__(self) -> None:
        """Initialize the back button for permissions step."""
        super().__init__(
            label="Back",
            style=discord.ButtonStyle.secondary,
            id=207,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle back button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"⬅️ BACK BUTTON CLICKED (Permissions)! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            wizard_view.build_welcome_step()
            await interaction.response.edit_message(view=cast("SetupWizardView", wizard_view))
        except Exception as e:
            logger.error(f"Failed to go back to welcome step: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to go back: {e}", ephemeral=True)


class ContinueButtonChannels(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Continue button for the channels step."""

    def __init__(self) -> None:
        """Initialize the continue button for channels step."""
        super().__init__(
            label="Continue",
            style=discord.ButtonStyle.primary,
            id=320,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle continue button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"🔄 CONTINUE BUTTON CLICKED (Channels)! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            wizard_view.current_step = 3
            wizard_view.build_roles_step()
            await interaction.response.edit_message(view=cast("SetupWizardView", wizard_view))
        except Exception as e:
            logger.error(f"Failed to move to roles step: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to continue: {e}", ephemeral=True)


class BackButtonChannels(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Back button for the channels step."""

    def __init__(self) -> None:
        """Initialize the back button for channels step."""
        super().__init__(
            label="Back",
            style=discord.ButtonStyle.secondary,
            id=321,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle back button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"⬅️ BACK BUTTON CLICKED (Channels)! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            wizard_view.current_step = 1
            wizard_view.build_permissions_step()
            await interaction.response.edit_message(view=cast("SetupWizardView", wizard_view))
        except Exception as e:
            logger.error(f"Failed to go back to permissions step: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to go back: {e}", ephemeral=True)


class ContinueButtonRoles(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Continue button for the roles step."""

    def __init__(self) -> None:
        """Initialize the continue button for roles step."""
        super().__init__(
            label="Continue",
            style=discord.ButtonStyle.primary,
            id=417,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle continue button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"🔄 CONTINUE BUTTON CLICKED (Roles)! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            await wizard_view.complete_setup(interaction)
        except Exception as e:
            logger.error(f"Failed to complete setup: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to complete setup: {e}", ephemeral=True)


class BackButtonRoles(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Back button for the roles step."""

    def __init__(self) -> None:
        """Initialize the back button for roles step."""
        super().__init__(
            label="Back",
            style=discord.ButtonStyle.secondary,
            id=418,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle back button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"⬅️ BACK BUTTON CLICKED (Roles)! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            wizard_view.current_step = 2
            wizard_view.build_channels_step()
            await interaction.response.edit_message(view=cast("SetupWizardView", wizard_view))
        except Exception as e:
            logger.error(f"Failed to go back to channels step: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to go back: {e}", ephemeral=True)


class FinishButton(WizardComponent, discord.ui.Button["SetupWizardView"]):
    """Finish button for the completion step."""

    def __init__(self) -> None:
        """Initialize the finish button."""
        super().__init__(
            label="Finish",
            style=discord.ButtonStyle.success,
            emoji="🎉",
            id=512,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle finish button click."""
        wizard_view = self.validate_wizard_context(interaction)
        if wizard_view is None:
            return

        if not self.validate_wizard_author(interaction, wizard_view):
            await interaction.response.send_message("❌ Only the setup author can control this wizard.", ephemeral=True)
            return

        logger.info(f"🎉 FINISH BUTTON CLICKED! User: {interaction.user}, Guild: {wizard_view.guild.id}")

        try:
            # Cast to SetupWizardView to access LayoutView methods
            setup_wizard = cast("SetupWizardView", wizard_view)

            # Replace the completion step content with finished message
            setup_wizard.clear_items()

            finished_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
                accent_color=0x00FF00,  # Green accent for success
                id=700,
            )

            finished_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
                "# ✅ Setup Complete!",
                id=701,
            )
            finished_container.add_item(finished_title)

            finished_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
                "Your server has been configured and is ready to use Tux!",
                id=702,
            )
            finished_container.add_item(finished_text)

            setup_wizard.add_item(finished_container)

            # Edit the Components V2 message to show finished state
            await interaction.response.edit_message(view=setup_wizard)

            # Stop the wizard
            setup_wizard.stop()

            # Schedule deletion after 30 seconds
            async def delete_after_delay():
                """
                Delete the finished wizard message after a delay.

                This coroutine waits 30 seconds after completion and then
                deletes the wizard message to keep the channel clean.
                """
                await asyncio.sleep(30)
                try:
                    if interaction.message:
                        await interaction.message.delete()
                        logger.info(f"Deleted finished Components V2 message for guild {setup_wizard.guild.id}")
                except Exception as delete_error:
                    logger.warning(f"Failed to delete finished message: {delete_error}")

            # Create background task for deletion
            delete_task = asyncio.create_task(delete_after_delay())

            delete_task.add_done_callback(
                lambda _: logger.info(f"Deleted finished Components V2 message for guild {setup_wizard.guild.id}"),
            )

        except Exception as e:
            logger.error(f"Failed to finish setup: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ Failed to finish setup: {e}", ephemeral=True)
