from datetime import datetime
from enum import Enum

import discord
from bot import Tux
from loguru import logger
from utils.config import Config
from utils.constants import CONST


class EmbedType(Enum):
    DEFAULT = 1
    INFO = 2
    ERROR = 3
    WARNING = 4
    SUCCESS = 5
    POLL = 6
    CASE = 7
    NOTE = 8


class EmbedCreator:
    DEFAULT: EmbedType = EmbedType.DEFAULT
    INFO: EmbedType = EmbedType.INFO
    ERROR: EmbedType = EmbedType.ERROR
    WARNING: EmbedType = EmbedType.WARNING
    SUCCESS: EmbedType = EmbedType.SUCCESS
    POLL: EmbedType = EmbedType.POLL
    CASE: EmbedType = EmbedType.CASE
    NOTE: EmbedType = EmbedType.NOTE

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
        """

        try:
            embed: discord.Embed = discord.Embed(title=title, description=description)

            type_settings: dict[EmbedType, tuple[int, str, str]] = {
                EmbedType.DEFAULT: (CONST.EMBED_COLORS["DEFAULT"], CONST.EMBED_ICONS["DEFAULT"], "Default"),
                EmbedType.INFO: (CONST.EMBED_COLORS["INFO"], CONST.EMBED_ICONS["INFO"], "Info"),
                EmbedType.ERROR: (CONST.EMBED_COLORS["ERROR"], CONST.EMBED_ICONS["ERROR"], "Error"),
                EmbedType.WARNING: (CONST.EMBED_COLORS["WARNING"], CONST.EMBED_ICONS["DEFAULT"], "Warning"),
                EmbedType.SUCCESS: (CONST.EMBED_COLORS["SUCCESS"], CONST.EMBED_ICONS["SUCCESS"], "Success"),
                EmbedType.POLL: (CONST.EMBED_COLORS["POLL"], CONST.EMBED_ICONS["POLL"], "Poll"),
                EmbedType.CASE: (CONST.EMBED_COLORS["CASE"], CONST.EMBED_ICONS["CASE"], "Case"),
                EmbedType.NOTE: (CONST.EMBED_COLORS["NOTE"], CONST.EMBED_ICONS["NOTE"], "Note"),
            }

            embed.color = custom_color or type_settings[embed_type][0]

            if not hide_author:
                embed.set_author(
                    name=custom_author_text or type_settings[embed_type][2],
                    icon_url=custom_author_icon_url or type_settings[embed_type][1],
                    url=custom_author_text_url,
                )

            if custom_footer_text:
                embed.set_footer(text=custom_footer_text, icon_url=custom_footer_icon_url)
            else:
                footer: tuple[str, str | None] = EmbedCreator.get_footer(bot, user_name, user_display_avatar)
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
        try:
            text: str = (
                f"{user_name}@discord $" if user_name else f"{Config.BOT_NAME.lower()}@discord $"
            )  # TODO: Make this configurable with the new config system.
            text += f" {round(bot.latency * 1000)}ms" if bot else ""

        except Exception as e:
            logger.debug("Error in get_footer", exc_info=e)
            raise

        else:
            return (
                text,
                user_display_avatar
                or "https://github.com/allthingslinux/tux/blob/main/assets/branding/avatar.png?raw=true",
            )
