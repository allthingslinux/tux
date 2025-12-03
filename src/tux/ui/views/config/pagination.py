"""
Pagination helpers for config dashboard modes.

Provides reusable pagination navigation builders, handlers, and setup utilities
to eliminate duplication across different dashboard modes.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine
from typing import TYPE_CHECKING, Any

import discord

if TYPE_CHECKING:
    from .dashboard import ConfigDashboard


class PaginationHelper:
    """Helper class for building pagination navigation and handling page changes."""

    @staticmethod
    def initialize_page_attr(dashboard: ConfigDashboard, attr_name: str) -> None:
        """
        Initialize a page attribute if it doesn't exist.

        Parameters
        ----------
        dashboard : ConfigDashboard
            The dashboard instance
        attr_name : str
            The attribute name (e.g., "ranks_current_page")
        """
        if not hasattr(dashboard, attr_name):
            setattr(dashboard, attr_name, 0)

    @staticmethod
    def calculate_pagination(
        total_items: int,
        items_per_page: int,
        current_page: int,
    ) -> tuple[int, int, int, int]:
        """
        Calculate pagination indices and total pages.

        Parameters
        ----------
        total_items : int
            Total number of items to paginate
        items_per_page : int
            Number of items per page
        current_page : int
            Current page index (0-based)

        Returns
        -------
        tuple[int, int, int, int]
            Tuple of (start_idx, end_idx, total_pages, validated_current_page)
        """
        total_pages = (
            total_items + items_per_page - 1
        ) // items_per_page  # Ceiling division

        # Ensure current page is valid
        if current_page >= total_pages:
            current_page = 0

        # Calculate which items to show on current page
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)

        return start_idx, end_idx, total_pages, current_page

    @staticmethod
    def setup_pagination(
        dashboard: ConfigDashboard,
        current_page_attr: str,
        total_items: int,
        items_per_page: int,
    ) -> tuple[int, int, int, int]:
        """
        Initialize pagination attributes and calculate pagination state.

        Parameters
        ----------
        dashboard : ConfigDashboard
            The dashboard instance
        current_page_attr : str
            Attribute name for current page (e.g., "ranks_current_page")
        total_items : int
            Total number of items to paginate
        items_per_page : int
            Number of items per page

        Returns
        -------
        tuple[int, int, int, int]
            Tuple of (start_idx, end_idx, total_pages, validated_current_page)
        """
        PaginationHelper.initialize_page_attr(dashboard, current_page_attr)
        current_page = getattr(dashboard, current_page_attr, 0)

        start_idx, end_idx, total_pages, validated_page = (
            PaginationHelper.calculate_pagination(
                total_items,
                items_per_page,
                current_page,
            )
        )

        # Update validated page back to dashboard
        setattr(dashboard, current_page_attr, validated_page)

        return start_idx, end_idx, total_pages, validated_page

    @staticmethod
    def build_navigation(
        mode_prefix: str,
        current_page: int,
        total_pages: int,
        page_change_handler: Callable[[discord.Interaction], Coroutine[Any, Any, None]],
    ) -> discord.ui.ActionRow[discord.ui.LayoutView]:
        """
        Build pagination navigation buttons for a mode.

        Parameters
        ----------
        mode_prefix : str
            Prefix for custom IDs (e.g., "ranks", "roles", "commands")
        current_page : int
            Current page index (0-based)
        total_pages : int
            Total number of pages
        page_change_handler : Callable
            Handler function for page change interactions

        Returns
        -------
        discord.ui.ActionRow[discord.ui.LayoutView]
            ActionRow containing navigation buttons
        """
        nav_row = discord.ui.ActionRow[discord.ui.LayoutView]()

        # First page button
        first_btn = discord.ui.Button[discord.ui.LayoutView](
            label="⏮️ First",
            style=discord.ButtonStyle.secondary,
            custom_id=f"{mode_prefix}_nav_first",
            disabled=current_page == 0,
        )
        first_btn.callback = page_change_handler  # type: ignore[assignment]
        nav_row.add_item(first_btn)

        # Previous page button
        prev_btn = discord.ui.Button[discord.ui.LayoutView](
            label="⬅️ Previous",
            style=discord.ButtonStyle.secondary,
            custom_id=f"{mode_prefix}_nav_prev",
            disabled=current_page == 0,
        )
        prev_btn.callback = page_change_handler  # type: ignore[assignment]
        nav_row.add_item(prev_btn)

        # Next page button
        next_btn = discord.ui.Button[discord.ui.LayoutView](
            label="➡️ Next",
            style=discord.ButtonStyle.secondary,
            custom_id=f"{mode_prefix}_nav_next",
            disabled=current_page >= total_pages - 1,
        )
        next_btn.callback = page_change_handler  # type: ignore[assignment]
        nav_row.add_item(next_btn)

        # Last page button
        last_btn = discord.ui.Button[discord.ui.LayoutView](
            label="⏭️ Last",
            style=discord.ButtonStyle.secondary,
            custom_id=f"{mode_prefix}_nav_last",
            disabled=current_page >= total_pages - 1,
        )
        last_btn.callback = page_change_handler  # type: ignore[assignment]
        nav_row.add_item(last_btn)

        return nav_row

    @staticmethod
    async def handle_page_change(
        interaction: discord.Interaction,
        dashboard: ConfigDashboard,
        mode_prefix: str,
        current_page_attr: str,
        total_pages_attr: str,
        rebuild_method: Callable[[], Awaitable[None]],
    ) -> None:
        """
        Handle pagination button clicks.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event
        dashboard : ConfigDashboard
            The dashboard instance
        mode_prefix : str
            Prefix for custom IDs
        current_page_attr : str
            Attribute name for current page (e.g., "ranks_current_page")
        total_pages_attr : str
            Attribute name for total pages (e.g., "ranks_total_pages")
        rebuild_method : Callable
            Async method to rebuild the mode after page change
        """
        if interaction.user != dashboard.author:
            await interaction.response.send_message(
                "❌ You are not authorized to navigate this configuration.",
                ephemeral=True,
            )
            return

        if not interaction.data:
            await interaction.response.send_message(
                "❌ Invalid interaction data",
                ephemeral=True,
            )
            return

        custom_id = interaction.data.get("custom_id", "")
        current_page = getattr(dashboard, current_page_attr, 0)
        total_pages = getattr(dashboard, total_pages_attr, 1)

        # Update page index
        if custom_id == f"{mode_prefix}_nav_first":
            setattr(dashboard, current_page_attr, 0)
        elif custom_id == f"{mode_prefix}_nav_prev":
            setattr(dashboard, current_page_attr, max(0, current_page - 1))
        elif custom_id == f"{mode_prefix}_nav_next":
            setattr(
                dashboard,
                current_page_attr,
                min(total_pages - 1, current_page + 1),
            )
        elif custom_id == f"{mode_prefix}_nav_last":
            setattr(dashboard, current_page_attr, total_pages - 1)

        # Invalidate cache and rebuild
        dashboard.invalidate_cache()
        await rebuild_method()
        await interaction.response.edit_message(view=dashboard)
