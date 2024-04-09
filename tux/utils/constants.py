import json
import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv()
config_file = Path("config/settings.json")
config = json.loads(config_file.read_text())


class Constants:
    # Bot-related constants
    BOT_VERSION = "1.0.0"
    BOT_NAME = "Tux"
    BOT_SOURCE = "https://github.com/allthingslinux/tux"

    # Production constants
    PROD_TOKEN: Final[str] = os.getenv("PROD_TOKEN", "")
    PROD_PREFIX: Final[str] = os.getenv("PROD_PREFIX", "$")
    PROD_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("PROD_COG_IGNORE_LIST", "").split(","))

    # Staging constants
    STAGING: Final[str | None] = os.getenv("STAGING")
    STAGING_TOKEN: Final[str] = os.getenv("STAGING_TOKEN", "")
    STAGING_PREFIX: Final[str] = os.getenv("STAGING_PREFIX", ">")
    STAGING_COG_IGNORE_LIST: Final[set[str]] = set(
        os.getenv("STAGING_COG_IGNORE_LIST", "").split(",")
    )

    # Sentry-related constants
    SENTRY_URL: Final[str | None] = os.getenv("SENTRY_URL")

    # Channel constants
    LOG_CHANNELS: Final[dict[str, int]] = {
        "AUDIT": 1223690612822376529,
        "MOD": 1223690612822376529,
    }

    # User ID Constants
    USER_IDS: Final[dict[str, int]] = {
        "ADMIN": config["Permissions"]["Admin"],
        "MOD": config["Permissions"]["Mod"],
        "JR MOD": config["Permissions"]["Jr_Mod"],
        "OWNER": config["Permissions"]["Owner"],
        "TESTING": config["Permissions"]["Testing"],
    }

    # Temp VC constants
    TEMPVC_CATEGORY_ID: Final[str | None] = os.getenv("TEMPVC_CATEGORY_ID")
    TEMPVC_CHANNEL_ID: Final[str | None] = os.getenv("TEMPVC_CHANNEL_ID")

    # Color constants
    EMBED_STATE_COLORS: Final[dict[str, int]] = {
        # tux feet yellow
        "DEFAULT": 0xF4D01A,
        # tux feet yellow
        "LOG": 0xF4D01A,
        # catppuccin mocha sky
        "INFO": 0x89DCEB,
        # catppuccin latte peach
        "WARNING": 0xFE640B,
        # catppuccin latte red
        "ERROR": 0xD20F39,
        # catppuccin mocha green
        "SUCCESS": 0xA6E3A1,
        # catppuccin mocha mauve
        "DEBUG": 0xCBA6F7,
        # pure black
        "BLACK": 0x000000,
        # pure white
        "WHITE": 0xFFFFFF,
        # catppuccin yellow
        "POLL": 0xF9E2AF,
    }

    EMBED_STATE_ICONS: Final[dict[str, str]] = {
        "DEFAULT": "https://i.imgur.com/EqzIMKr.png",
        "LOG": "https://i.imgur.com/4sblrd0.png",
        "INFO": "https://github.com/catppuccin/catppuccin/blob/main/assets/palette/circles/mocha_sky.png?raw=true",
        "WARNING": "https://github.com/catppuccin/catppuccin/raw/main/assets/palette/circles/latte_peach.png?raw=true",
        "ERROR": "https://github.com/catppuccin/catppuccin/blob/main/assets/palette/circles/latte_red.png?raw=true",
        "SUCCESS": "https://github.com/catppuccin/catppuccin/blob/main/assets/palette/circles/mocha_green.png?raw=true",
        "POLL": "https://github.com/catppuccin/catppuccin/raw/main/assets/palette/circles/mocha_yellow.png?raw=true",
    }

    EMBED_SPECIAL_CHARS: Final[dict[str, str]] = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "EMPTY": "​",
    }

    # Embed limit constants
    EMBED_MAX_NAME_LENGTH = 256
    EMBED_MAX_DESC_LENGTH = 4096
    EMBED_MAX_FIELDS = 25
    EMBED_TOTAL_MAX = 6000
    EMBED_FIELD_VALUE_LENGTH = 1024

    # Interaction constants
    ACTION_ROW_MAX_ITEMS = 5
    SELECTS_MAX_OPTIONS = 25
    SELECT_MAX_NAME_LENGTH = 100

    # App commands constants
    CONTEXT_MENU_NAME_LENGTH = 32
    SLASH_CMD_NAME_LENGTH = 32
    SLASH_CMD_MAX_DESC_LENGTH = 100
    SLASH_CMD_MAX_OPTIONS = 25
    SLASH_OPTION_NAME_LENGTH = 100


"""
Constants for the bot.

Example:

from tux.utils.constants import Constants as CONST
print(CONST.BOT_NAME)
print(CONST.EMBED_STATE_COLORS["INFO"])
print(CONST.CHANNELS["AUDIT"])
"""

CONST = Constants()
