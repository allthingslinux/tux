"""Components V2 views for info command displays."""

from collections.abc import Iterable
from contextlib import suppress

import discord

from tux.modules.info.helpers import chunks


class InfoPaginatorView(discord.ui.LayoutView):
    """Components V2 pagination view for info command lists.

    Replaces reactionmenu.ViewMenu with a Components V2 implementation.
    """

    # Component IDs for dynamic updates
    CONTENT_ID = 1000
    PAGE_INFO_ID = 1001

    items: list[str]
    chunks_list: list[list[str]]
    current_page: int
    title: str
    list_type: str
    guild_name: str

    def __init__(
        self,
        items: Iterable[str],
        title: str,
        list_type: str,
        guild_name: str,
        chunk_size: int = 50,
        timeout: float = 300.0,
    ) -> None:
        """Initialize the paginator view.

        Parameters
        ----------
        items : Iterable[str]
            The items to paginate.
        title : str
            The title of the paginated view.
        list_type : str
            The type of list (e.g., "roles", "emojis").
        guild_name : str
            The name of the guild.
        chunk_size : int, optional
            The size of each chunk, by default 50.
        timeout : float, optional
            View timeout in seconds, by default 300.0.
        """
        if chunk_size < 1:
            error_msg = "chunk_size must be >= 1"
            raise ValueError(error_msg)
        super().__init__(timeout=timeout)
        self.items = list(items)
        self.chunks_list: list[list[str]] = list(chunks(iter(self.items), chunk_size))
        self.current_page = 0
        self.title = title
        self.list_type = list_type
        self.guild_name = guild_name
        self._build_layout()

    def _build_layout(self) -> None:
        """Build the initial layout with content and navigation."""
        self.clear_items()

        container = discord.ui.Container[discord.ui.LayoutView](accent_color=0x5865F2)

        # Title and content combined
        if not self.chunks_list:
            content_text = "No items available."
        else:
            current_chunk = self.chunks_list[self.current_page]
            content_text = (
                f"### {self.list_type.capitalize()} list for {self.guild_name}\n\n"
                f"{' '.join(current_chunk)}"
            )

        container.add_item(
            discord.ui.TextDisplay(
                f"# {self.title}\n\n{content_text}",
                id=self.CONTENT_ID,
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Page info
        container.add_item(
            discord.ui.TextDisplay(
                self._get_page_info(),
                id=self.PAGE_INFO_ID,
            ),
        )

        self.add_item(container)

        # Navigation buttons
        if len(self.chunks_list) > 1:
            nav_row = self._build_navigation()
            self.add_item(nav_row)

    def _get_page_info(self) -> str:
        """Get the page information text.

        Returns
        -------
        str
            The page info text.
        """
        if not self.chunks_list:
            return "*No pages*"
        total_pages = len(self.chunks_list)
        return f"*Page {self.current_page + 1} of {total_pages}*"

    def _build_navigation(self) -> discord.ui.ActionRow[discord.ui.LayoutView]:
        """Build navigation buttons for pagination.

        Returns
        -------
        discord.ui.ActionRow[discord.ui.LayoutView]
            ActionRow containing navigation buttons.
        """
        nav_row = discord.ui.ActionRow[discord.ui.LayoutView]()

        total_pages = len(self.chunks_list)

        # First page button
        first_btn = discord.ui.Button[discord.ui.LayoutView](
            label="⏮️ First",
            style=discord.ButtonStyle.secondary,
            custom_id="info_paginator_first",
            disabled=self.current_page == 0,
        )
        first_btn.callback = self._handle_first
        nav_row.add_item(first_btn)

        # Previous page button
        prev_btn = discord.ui.Button[discord.ui.LayoutView](
            label="⬅️ Previous",
            style=discord.ButtonStyle.secondary,
            custom_id="info_paginator_prev",
            disabled=self.current_page == 0,
        )
        prev_btn.callback = self._handle_prev
        nav_row.add_item(prev_btn)

        # Next page button
        next_btn = discord.ui.Button[discord.ui.LayoutView](
            label="➡️ Next",
            style=discord.ButtonStyle.secondary,
            custom_id="info_paginator_next",
            disabled=self.current_page >= total_pages - 1,
        )
        next_btn.callback = self._handle_next
        nav_row.add_item(next_btn)

        # Last page button
        last_btn = discord.ui.Button[discord.ui.LayoutView](
            label="⏭️ Last",
            style=discord.ButtonStyle.secondary,
            custom_id="info_paginator_last",
            disabled=self.current_page >= total_pages - 1,
        )
        last_btn.callback = self._handle_last
        nav_row.add_item(last_btn)

        # Close button
        close_btn = discord.ui.Button[discord.ui.LayoutView](
            label="❌ Close",
            style=discord.ButtonStyle.danger,
            custom_id="info_paginator_close",
        )
        close_btn.callback = self._handle_close
        nav_row.add_item(close_btn)

        return nav_row

    async def _handle_first(self, interaction: discord.Interaction) -> None:
        """Handle first page button click."""
        if self.current_page == 0:
            await interaction.response.defer()
            return

        self.current_page = 0
        await self._update_page(interaction)

    async def _handle_prev(self, interaction: discord.Interaction) -> None:
        """Handle previous page button click."""
        if self.current_page == 0:
            await interaction.response.defer()
            return

        self.current_page -= 1
        await self._update_page(interaction)

    async def _handle_next(self, interaction: discord.Interaction) -> None:
        """Handle next page button click."""
        if self.current_page >= len(self.chunks_list) - 1:
            await interaction.response.defer()
            return

        self.current_page += 1
        await self._update_page(interaction)

    async def _handle_last(self, interaction: discord.Interaction) -> None:
        """Handle last page button click."""
        if self.current_page >= len(self.chunks_list) - 1:
            await interaction.response.defer()
            return

        self.current_page = len(self.chunks_list) - 1
        await self._update_page(interaction)

    async def _handle_close(self, interaction: discord.Interaction) -> None:
        """Handle close button click."""
        await interaction.response.defer()
        with suppress(discord.NotFound):
            # Message may have already been deleted
            await interaction.delete_original_response()

    async def _update_page(self, interaction: discord.Interaction) -> None:
        """Update the view with the current page content.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction to respond to.
        """
        # Update content
        content_display = self.find_item(self.CONTENT_ID)
        if isinstance(content_display, discord.ui.TextDisplay):
            if not self.chunks_list:
                content_text = "No items available."
            else:
                current_chunk = self.chunks_list[self.current_page]
                content_text = (
                    f"### {self.list_type.capitalize()} list for {self.guild_name}\n\n"
                    f"{' '.join(current_chunk)}"
                )
            content_display.content = f"# {self.title}\n\n{content_text}"

        # Update page info
        page_info = self.find_item(self.PAGE_INFO_ID)
        if isinstance(page_info, discord.ui.TextDisplay):
            page_info.content = self._get_page_info()

        # Update navigation buttons
        self._update_navigation_buttons()

        await interaction.response.edit_message(view=self)

    def _update_navigation_buttons(self) -> None:
        """Update navigation button states based on current page."""
        total_pages = len(self.chunks_list)

        # Find the navigation ActionRow
        nav_row = next(
            (
                item
                for item in self.walk_children()
                if isinstance(item, discord.ui.ActionRow)
            ),
            None,
        )

        if nav_row is None:
            return

        # Update button states
        for button in nav_row.children:
            if not isinstance(button, discord.ui.Button):
                continue

            custom_id = button.custom_id
            if custom_id in ("info_paginator_first", "info_paginator_prev"):
                button.disabled = self.current_page == 0
            elif custom_id in ("info_paginator_next", "info_paginator_last"):
                button.disabled = self.current_page >= total_pages - 1
