"""
Helper utilities for config dashboard.

Provides common UI building patterns, error handling, and utility functions
to reduce duplication across dashboard modes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from .dashboard import ConfigDashboard


def create_back_button(
    dashboard: ConfigDashboard,
) -> discord.ui.Button[discord.ui.LayoutView]:
    """
    Create a standardized "Back to Dashboard" button.

    Parameters
    ----------
    dashboard : ConfigDashboard
        The dashboard instance to attach the callback to

    Returns
    -------
    discord.ui.Button[discord.ui.LayoutView]
        Configured back button
    """
    back_btn = discord.ui.Button[discord.ui.LayoutView](
        label="⬅️ Back to Dashboard",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_back_overview",
    )
    back_btn.callback = dashboard.handle_back_to_overview
    return back_btn


def create_error_container(
    error_message: str,
    dashboard: ConfigDashboard,
) -> discord.ui.Container[discord.ui.LayoutView]:
    """
    Create a standardized error container with back button.

    Parameters
    ----------
    error_message : str
        Error message to display
    dashboard : ConfigDashboard
        Dashboard instance for callback

    Returns
    -------
    discord.ui.Container[discord.ui.LayoutView]
        Error container with message and back button
    """
    error_container = discord.ui.Container[discord.ui.LayoutView](
        accent_color=0xED4245,  # Discord red
    )

    error_display = discord.ui.TextDisplay[discord.ui.LayoutView](f"❌ {error_message}")
    error_container.add_item(error_display)

    back_btn = create_back_button(dashboard)
    actions_row = discord.ui.ActionRow[discord.ui.LayoutView]()
    actions_row.add_item(back_btn)
    error_container.add_item(actions_row)

    return error_container


def add_back_button_to_container(
    container: discord.ui.Container[discord.ui.LayoutView],
    dashboard: ConfigDashboard,
) -> None:
    """
    Add a back button to a container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        Container to add button to
    dashboard : ConfigDashboard
        Dashboard instance for callback
    """
    back_btn = create_back_button(dashboard)
    actions_row = discord.ui.ActionRow[discord.ui.LayoutView]()
    actions_row.add_item(back_btn)
    container.add_item(actions_row)
