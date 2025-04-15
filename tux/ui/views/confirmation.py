import discord

# Confirmation dialog view:
# This view is to be used for a confirmation dialog.
# ideally it should be sent as a DM to ensure the user requesting it is the only one able to interact.
# The base class implements the buttons themselves,
# and the subclasses, which are intended to be imported and used in cogs,
# change the style and labels depending on severity of the action being confirmed.


class BaseConfirmationView(discord.ui.View):
    confirm_label: str
    confirm_style: discord.ButtonStyle

    def __init__(self, user: int) -> None:
        super().__init__()
        self.value: bool | None = None
        self.user = user

    @discord.ui.button(label="PLACEHOLDER", style=discord.ButtonStyle.secondary, custom_id="confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        if interaction.user.id is not self.user:
            await interaction.response.send_message("This interaction is locked to the command author.", ephemeral=True)
            return
        await interaction.response.send_message("Confirming", ephemeral=True)
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]) -> None:
        if interaction.user.id is not self.user:
            await interaction.response.send_message("This interaction is locked to the command author.", ephemeral=True)
            return
        await interaction.response.send_message("Cancelling", ephemeral=True)
        self.value = False
        self.stop()

    def update_button_styles(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "confirm":
                item.label = self.confirm_label
                item.style = self.confirm_style


class ConfirmationDanger(BaseConfirmationView):
    def __init__(self, user: int) -> None:
        super().__init__(user)
        self.confirm_label = "I understand and wish to proceed anyway"
        self.confirm_style = discord.ButtonStyle.danger
        self.update_button_styles()


class ConfirmationNormal(BaseConfirmationView):
    def __init__(self, user: int) -> None:
        super().__init__(user)
        self.confirm_label = "Confirm"
        self.confirm_style = discord.ButtonStyle.green
        self.update_button_styles()
