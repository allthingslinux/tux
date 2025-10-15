"""Base classes and utilities for onboarding wizard components."""

from __future__ import annotations

from typing import Any, Protocol

import discord
from loguru import logger

# Type checking imports can be added here if needed


class WizardViewProtocol(Protocol):
    """Protocol defining the interface expected from wizard views."""

    guild: discord.Guild
    author: discord.User
    current_step: int

    # Required methods for wizard functionality
    def build_permissions_step(self) -> None: ...
    def build_channels_step(self) -> None: ...
    def build_roles_step(self) -> None: ...
    def build_welcome_step(self) -> None: ...
    async def initialize_permissions(self, interaction: discord.Interaction) -> Any: ...
    async def complete_setup(self, interaction: discord.Interaction) -> Any: ...

    # Channel selection callbacks
    async def on_mod_log_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_audit_log_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_join_log_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_private_log_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_report_log_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_dev_log_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_jail_channel_select(self, interaction: discord.Interaction) -> None: ...
    async def on_jail_role_select(self, interaction: discord.Interaction) -> None: ...
    async def on_permission_rank_role_select(
        self,
        interaction: discord.Interaction,
        rank: int,
        values: list[discord.Role],
    ) -> None: ...

    # LayoutView methods
    def stop(self) -> None: ...


class WizardComponent:
    """Base class for wizard components with common validation logic."""

    def validate_wizard_context(self, interaction: discord.Interaction) -> WizardViewProtocol | None:
        """Validate the interaction is from a valid wizard context.

        Returns
        -------
            The wizard view if valid, None otherwise.
        """
        view = self.view  # type: ignore
        if view is None:
            return None

        # Duck typing check for required wizard view attributes
        if not (hasattr(view, "guild") and hasattr(view, "author") and hasattr(view, "current_step")):  # type: ignore
            return None

        return view  # type: ignore

    def validate_wizard_author(self, interaction: discord.Interaction, wizard_view: WizardViewProtocol) -> bool:
        """Validate that the interaction user is the wizard author.

        Returns
        -------
            True if authorized, False otherwise.
        """
        if interaction.user != wizard_view.author:
            logger.warning(
                f"Unauthorized user {interaction.user} tried to control wizard for guild {wizard_view.guild.id}",
            )
            return False
        return True
