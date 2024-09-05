from datetime import datetime
from enum import Enum

import discord
from loguru import logger

from tux.bot import Tux
from tux.utils.constants import Constants as CONST


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
        message_timestamp: datetime | None = None,
        custom_footer: tuple[str, str | None] | None = None,
    ) -> discord.Embed:
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

            embed.color = type_settings[embed_type][0]

            embed.set_author(
                name=type_settings[embed_type][2],
                icon_url=type_settings[embed_type][1],
            )

            if custom_footer:
                embed.set_footer(text=custom_footer[0], icon_url=custom_footer[1])
            else:
                footer: tuple[str, str | None] = EmbedCreator.get_footer(bot, user_name, user_display_avatar)
                embed.set_footer(text=footer[0], icon_url=footer[1])

            embed.timestamp = message_timestamp or discord.utils.utcnow()

        except Exception as e:
            logger.debug(f"Error in create_embed: {e!r}")
            raise

        else:
            return embed

    @staticmethod
    def create_error_embed(
        bot: Tux | None = None,
        error: str = "An error occurred",
    ) -> discord.Embed:
        try:
            embed: discord.Embed = EmbedCreator.create_embed(
                bot=bot,
                embed_type=EmbedType.ERROR,
                description=f"<:tux_error:1273494919897681930> {error}",
            )
        except Exception as e:
            logger.debug(f"Error in create_error_embed: {e!r}")
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
            text: str = f"{user_name}@atl $" if user_name else "tux@atl $"
            text += f" {round(bot.latency * 1000)}ms" if bot else ""

        except Exception as e:
            logger.debug(f"Error in get_footer: {e!r}")
            raise

        else:
            return (text, user_display_avatar or "https://i.imgur.com/4sblrd0.png")
