import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()


class Constants:
    # Bot-related constants
    BOT_VERSION = "1.0.0"
    BOT_NAME = "Tux"
    BOT_SOURCE = "https://github.com/allthingslinux/tux"

    # Discord-related constants
    PROD_TOKEN: Final[str] = os.getenv("PROD_TOKEN", "")
    STAGING_TOKEN: Final[str] = os.getenv("STAGING_TOKEN", "")

    # Sentry-related constants
    SENTRY_URL: Final[str] = os.getenv("SENTRY_URL", "")

    # Command constants
    PROD_PREFIX: Final[str] = os.getenv("PREFIX", "t!")
    STAGING_PREFIX: Final[str] = os.getenv("STAGING_PREFIX", "ts!")

    # Channel constants
    CHANNELS: Final[dict[str, int]] = {
        "audit": 1191472088695980083,
        "mod": 1234567890,
        "general": 1234567890,
        "bot": 1234567890,
    }

    # Color constants
    COLORS: Final[dict[str, int]] = {
        "default": 0xF2B033,
        "info": 0x00BFFF,
        "warning": 0xFFA500,
        "error": 0xFF0000,
        "success": 0x00FF00,
        "debug": 0x800080,
        "black": 0x000000,
        "white": 0xFFFFFF,
    }

    # Cog related constants
    PROD_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("PROD_COG_IGNORE_LIST", "").split(","))

    STAGING_COG_IGNORE_LIST: Final[set[str]] = set(
        os.getenv("STAGING_COG_IGNORE_LIST", "").split(",")
    )

    # Temp VC constants
    TEMPVC_CATEGORY_ID = os.getenv("TEMPVC_CATEGORY_ID")
    TEMPVC_CHANNEL_ID = os.getenv("TEMPVC_CHANNEL_ID")


"""
Constants for the bot.

Example:

from tux.constants import C
print(C.BOT_NAME)
print(C.COLORS.info)
print(C.CHANNELS.audit)
"""

C = Constants()
