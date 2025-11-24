"""
Discord Confirmation Views for Tux Bot.

This module provides confirmation dialog views for Discord interactions,
allowing users to confirm or cancel potentially destructive actions.
Views should ideally be sent as DMs to ensure only the requesting user can interact.
"""

import discord


class BaseConfirmationView(discord.ui.View):
    """Base confirmation view with confirm and cancel buttons."""

    confirm_label: str
    confirm_style: discord.ButtonStyle

    def __init__(self, user: int) -> None:
        """Initialize the base confirmation view.

        Parameters
        ----------
        user : int
            The user ID that can interact with this view.
        """
        super().__init__()
        self.value: bool | None = None
        self.user = user

    @discord.ui.button(
        label="PLACEHOLDER",
        style=discord.ButtonStyle.secondary,
        custom_id="confirm",
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ) -> None:
        """Handle the confirm button press.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered this action.
        button : discord.ui.Button[discord.ui.View]
            The button that was pressed.
        """
        if interaction.user.id is not self.user:
            await interaction.response.send_message(
                "This interaction is locked to the command author.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message("Confirming", ephemeral=True)
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ) -> None:
        """Handle the cancel button press.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered this action.
        button : discord.ui.Button[discord.ui.View]
            The button that was pressed.
        """
        if interaction.user.id is not self.user:
            await interaction.response.send_message(
                "This interaction is locked to the command author.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message("Cancelling", ephemeral=True)
        self.value = False
        self.stop()

    def update_button_styles(self) -> None:
        """Update button styles for the confirmation view."""
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "confirm":
                item.label = self.confirm_label
                item.style = self.confirm_style


class ConfirmationDanger(BaseConfirmationView):
    """Confirmation view with a danger button."""

    def __init__(self, user: int) -> None:
        """
        Initialize the danger confirmation view.

        Parameters
        ----------
        user : int
            The user ID that can interact with this view.
        """
        super().__init__(user)
        self.confirm_label = "I understand and wish to proceed anyway"
        self.confirm_style = discord.ButtonStyle.danger
        self.update_button_styles()


class ConfirmationNormal(BaseConfirmationView):
    """Confirmation view with a normal button."""

    def __init__(self, user: int) -> None:
        """
        Initialize the normal confirmation view.

        Parameters
        ----------
        user : int
            The user ID that can interact with this view.
        """
        super().__init__(user)
        self.confirm_label = "Confirm"
        self.confirm_style = discord.ButtonStyle.green
        self.update_button_styles()
