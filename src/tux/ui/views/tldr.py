"""
TLDR Paginator View.

A Discord UI view for paginating through long TLDR command documentation pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ui import Button, View

from tux.ui.embeds import EmbedCreator

if TYPE_CHECKING:
    from tux.core.bot import Tux


class TldrPaginatorView(View):
    """Paginator view for navigating through long TLDR pages."""

    def __init__(self, pages: list[str], title: str, user: discord.abc.User, bot: Tux):
        """Initialize the TLDR paginator view.

        Parameters
        ----------
        pages : list[str]
            List of page content strings to paginate through.
        title : str
            Title for the paginated content.
        user : discord.abc.User
            User who can interact with this view.
        bot : Tux
            Bot instance for embed creation.
        """
        super().__init__(timeout=120)
        self.pages = pages
        self.page = 0
        self.title = title
        self.user = user
        self.bot = bot
        self.message: discord.Message | None = None
        self.add_item(
            Button[View](
                label="Previous",
                style=discord.ButtonStyle.secondary,
                custom_id="prev",
            ),
        )
        self.add_item(
            Button[View](
                label="Next",
                style=discord.ButtonStyle.secondary,
                custom_id="next",
            ),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the interaction user is allowed to interact with this view.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction to check.

        Returns
        -------
        bool
            True if the user is allowed to interact.
        """
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        """Handle view timeout by removing the view from the message."""
        if self.message:
            await self.message.edit(view=None)

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        custom_id="prev",
    )
    async def prev(self, interaction: discord.Interaction, button: Button[View]):
        """Navigate to the previous page.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered this action.
        button : Button[View]
            The button that was pressed.
        """
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.secondary,
        custom_id="next",
    )
    async def next(self, interaction: discord.Interaction, button: Button[View]):
        """Navigate to the next page.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered this action.
        button : Button[View]
            The button that was pressed.
        """
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    async def update_message(self, interaction: discord.Interaction) -> None:
        """Update the message with the current page content.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction to update the message for.
        """
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=self.user.name,
            user_display_avatar=self.user.display_avatar.url,
            title=f"{self.title} (Page {self.page + 1}/{len(self.pages)})",
            description=self.pages[self.page],
        )
        await interaction.response.edit_message(embed=embed, view=self)
