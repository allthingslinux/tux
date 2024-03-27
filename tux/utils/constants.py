# tux/constants.py
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
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_GUILD = os.getenv("DISCORD_GUILD")

    # tempvc
    TEMPVC_CATEGORY = os.getenv("TEMPVC_CATEGORY")
    TEMPVC_CHANNEL = os.getenv("TEMPVC_CHANNEL")

    # Command constants
    PREFIX: Final[str] = ">"

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


"""
Constants for the bot.

Example:

from tux.constants import C
print(C.BOT_NAME)
print(C.COLORS.info)
print(C.CHANNELS.audit)
"""

C = Constants()
