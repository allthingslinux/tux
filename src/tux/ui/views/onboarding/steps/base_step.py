"""Base class for wizard steps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView
else:
    SetupWizardView = discord.ui.LayoutView


class BaseWizardStep(ABC):
    """Base class for all wizard steps."""

    def __init__(self, wizard: SetupWizardView) -> None:
        """Initialize the step with a reference to the wizard."""
        self.wizard = wizard

    @abstractmethod
    def build(self) -> None:
        """Build the step's UI components."""

    @property
    def bot(self) -> discord.Client:
        """Get the bot instance."""
        return self.wizard.bot

    @property
    def guild(self) -> discord.Guild:
        """Get the guild instance."""
        return self.wizard.guild

    @property
    def author(self) -> discord.User:
        """Get the author instance."""
        return self.wizard.author

    def clear_items(self) -> None:
        """Clear all items from the wizard view."""
        self.wizard.clear_items()

    def add_item(self, item: discord.ui.Item[SetupWizardView]) -> None:
        """Add an item to the wizard view."""
        self.wizard.add_item(item)
