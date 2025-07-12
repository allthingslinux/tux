"""
TLDR Paginator View.

A Discord UI view for paginating through long TLDR command documentation pages.
"""

import discord
from bot import Tux
from discord.ui import Button, View
from ui.embeds import EmbedCreator


class TldrPaginatorView(View):
    """Paginator view for navigating through long TLDR pages."""

    def __init__(self, pages: list[str], title: str, user: discord.abc.User, bot: Tux):
        super().__init__(timeout=120)
        self.pages = pages
        self.page = 0
        self.title = title
        self.user = user
        self.bot = bot
        self.message: discord.Message | None = None
        self.add_item(Button[View](label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev"))
        self.add_item(Button[View](label="Next", style=discord.ButtonStyle.secondary, custom_id="next"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev(self, interaction: discord.Interaction, button: Button[View]):
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: Button[View]):
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    async def update_message(self, interaction: discord.Interaction):
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=self.user.name,
            user_display_avatar=self.user.display_avatar.url,
            title=f"{self.title} (Page {self.page + 1}/{len(self.pages)})",
            description=self.pages[self.page],
        )
        await interaction.response.edit_message(embed=embed, view=self)
