"""
Discord Embed Creation Utilities for Tux Bot.

This module provides utilities for creating standardized Discord embeds
with consistent styling, colors, and formatting across the bot.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

import discord
from loguru import logger

if TYPE_CHECKING:  # Avoid runtime import cycle
    from tux.core.bot import Tux
from tux.shared.config import CONFIG
from tux.shared.constants import EMBED_COLORS, EMBED_ICONS


class EmbedType(Enum):
    """Enumeration of available embed types with predefined styles."""

    DEFAULT = 1
    INFO = 2
    ERROR = 3
    WARNING = 4
    SUCCESS = 5
    POLL = 6
    CASE = 7
    NOTE = 8
    ACTIVE_CASE = 9
    INACTIVE_CASE = 10


class EmbedCreator:
    """Utility class for creating standardized Discord embeds."""

    DEFAULT: EmbedType = EmbedType.DEFAULT
    INFO: EmbedType = EmbedType.INFO
    ERROR: EmbedType = EmbedType.ERROR
    WARNING: EmbedType = EmbedType.WARNING
    SUCCESS: EmbedType = EmbedType.SUCCESS
    POLL: EmbedType = EmbedType.POLL
    CASE: EmbedType = EmbedType.CASE
    NOTE: EmbedType = EmbedType.NOTE
    ACTIVE_CASE: EmbedType = EmbedType.ACTIVE_CASE
    INACTIVE_CASE: EmbedType = EmbedType.INACTIVE_CASE

    @staticmethod
    def create_embed(
        embed_type: EmbedType,
        bot: Tux | None = None,
        title: str | None = None,
        description: str | None = None,
        user_name: str | None = None,
        user_display_avatar: str | None = None,
        image_url: str | None = None,
        thumbnail_url: str | None = None,
        message_timestamp: datetime | None = None,
        custom_footer_text: str | None = None,
        custom_footer_icon_url: str | None = None,
        custom_author_text: str | None = None,
        custom_author_text_url: str | None = None,
        custom_author_icon_url: str | None = None,
        custom_color: int | discord.Colour | None = None,
        hide_author: bool = False,
        hide_timestamp: bool = False,
    ) -> discord.Embed:
        """
        Create a customized Discord embed based on the specified type and parameters.

        Parameters
        ----------
        embed_type : EmbedType
            Determines the default color and icon for the embed.
        bot : Tux, optional
            If provided, used to display bot latency in the footer.
        title : str, optional
            The embed's title. At least one of `title` or `description` should be provided.
        description : str, optional
            The embed's main content. At least one of `title` or `description` should be provided.
        user_name : str, optional
            Used in footer if provided, otherwise defaults to bot's username.
        user_display_avatar : str, optional
            User's avatar URL for the footer icon.
        image_url : str, optional
            URL for the embed's main image.
        thumbnail_url : str, optional
            URL for the embed's thumbnail image.
        message_timestamp : datetime, optional
            Custom timestamp for the embed.
        custom_footer_text : str, optional
            Overrides default footer text if provided.
        custom_footer_icon_url : str, optional
            Overrides default footer icon if provided.
        custom_author_text : str, optional
            Overrides default author text if provided.
        custom_author_text_url : str, optional
            Adds author URL if provided.
        custom_author_icon_url : str, optional
            Overrides default author icon if provided.
        hide_author : bool, default=False
            If True, removes the author from the embed.
        custom_color : int or Colour, optional
            Overrides default color for the embed type if provided.

        Returns
        -------
        discord.Embed
            The customized Discord embed.
        """
        try:
            embed: discord.Embed = discord.Embed(title=title, description=description)

            type_settings: dict[EmbedType, tuple[int, str, str]] = {
                EmbedType.DEFAULT: (
                    EMBED_COLORS["DEFAULT"],
                    EMBED_ICONS["DEFAULT"],
                    "Default",
                ),
                EmbedType.INFO: (EMBED_COLORS["INFO"], EMBED_ICONS["INFO"], "Info"),
                EmbedType.ERROR: (EMBED_COLORS["ERROR"], EMBED_ICONS["ERROR"], "Error"),
                EmbedType.WARNING: (
                    EMBED_COLORS["WARNING"],
                    EMBED_ICONS["DEFAULT"],
                    "Warning",
                ),
                EmbedType.SUCCESS: (
                    EMBED_COLORS["SUCCESS"],
                    EMBED_ICONS["SUCCESS"],
                    "Success",
                ),
                EmbedType.POLL: (EMBED_COLORS["POLL"], EMBED_ICONS["POLL"], "Poll"),
                EmbedType.CASE: (EMBED_COLORS["CASE"], EMBED_ICONS["CASE"], "Case"),
                EmbedType.ACTIVE_CASE: (
                    EMBED_COLORS["CASE"],
                    EMBED_ICONS["ACTIVE_CASE"],
                    "Active Case",
                ),
                EmbedType.INACTIVE_CASE: (
                    EMBED_COLORS["CASE"],
                    EMBED_ICONS["INACTIVE_CASE"],
                    "Inactive Case",
                ),
                EmbedType.NOTE: (EMBED_COLORS["NOTE"], EMBED_ICONS["NOTE"], "Note"),
            }

            embed.color = (
                type_settings[embed_type][0] if custom_color is None else custom_color
            )
            # Ensure color is a discord.Colour object
            if isinstance(embed.color, int):
                embed.color = discord.Colour(embed.color)  # type: ignore
            elif embed.color is None or not isinstance(embed.color, discord.Colour):
                embed.color = type_settings[embed_type][0]

            if not hide_author:
                embed.set_author(
                    name=custom_author_text or type_settings[embed_type][2],
                    icon_url=custom_author_icon_url or type_settings[embed_type][1],
                    url=custom_author_text_url,
                )

            if custom_footer_text:
                embed.set_footer(
                    text=custom_footer_text,
                    icon_url=custom_footer_icon_url,
                )
            else:
                footer: tuple[str, str | None] = EmbedCreator.get_footer(
                    bot,
                    user_name,
                    user_display_avatar,
                )
                embed.set_footer(text=footer[0], icon_url=footer[1])

            if image_url:
                embed.set_image(url=image_url)

            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)

            if not hide_timestamp:
                embed.timestamp = message_timestamp or discord.utils.utcnow()

        except Exception as e:
            logger.debug("Error in create_embed", exc_info=e)
            raise

        else:
            return embed

    @staticmethod
    def get_footer(
        bot: Tux | None = None,
        user_name: str | None = None,
        user_display_avatar: str | None = None,
    ) -> tuple[str, str | None]:
        """Generate footer text and icon for embeds.

        Parameters
        ----------
        bot : Tux, optional
            The bot instance to get latency from.
        user_name : str, optional
            Username to include in footer.
        user_display_avatar : str, optional
            User avatar URL for footer icon.

        Returns
        -------
        tuple[str, str | None]
            Tuple of (footer_text, avatar_url).
        """
        try:
            text: str = (
                f"{user_name}@discord $"
                if user_name
                else f"{CONFIG.BOT_INFO.BOT_NAME.lower()}@discord $"
            )  # TODO: Make this configurable with the new config system.
            text += f" {round(bot.latency * 1000)}ms" if bot else ""

        except Exception as e:
            logger.debug("Error in get_footer", exc_info=e)
            raise

        else:
            return (
                text,
                user_display_avatar
                or "https://github.com/allthingslinux/tux/blob/main/assets/branding/avatar.avif?raw=true",
            )
