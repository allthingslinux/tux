import base64
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
    BOT_OWNER_ID: Final[int] = int(os.getenv("BOT_OWNER_ID", 0))

    GITHUB_REPO_URL = "https://github.com/allthingslinux/tux"
    GITHUB_REPO_OWNER = "allthingslinux"
    GITHUB_REPO = "tux"
    GITHUB_TOKEN: Final[str] = os.getenv("GITHUB_TOKEN", "")
    GITHUB_APP_ID: Final[int] = int(os.getenv("GITHUB_APP_ID", 0))
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_PUBLIC_KEY = os.getenv("GITHUB_PUBLIC_KEY")
    GITHUB_INSTALLATION_ID: Final[int] = int(os.getenv("GITHUB_INSTALLATION_ID", 0))
    GITHUB_PRIVATE_KEY: str = base64.b64decode(os.getenv("GITHUB_PRIVATE_KEY_BASE64", "")).decode(
        "utf-8"
    )

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
        # For general logging
        "AUDIT": 1235096271350399076,
        # For infractions, mod actions, etc.
        "MOD": 1235096291672068106,
        # For anonymous reports
        "REPORTS": 1235096305160814652,
        # For gate logging
        "GATE": 1235096247442870292,
        # For tux logs (errors, debug, db, api, etc)
        "DEV": 1235096558463225887,
        # For private logs (voice, messages, etc)
        "PRIVATE": 1235108340791513129,
    }

    if str(STAGING).lower() == "true":
        LOG_CHANNELS["AUDIT"] = 1235095919788167269
        LOG_CHANNELS["MOD"] = 1235095919788167269
        LOG_CHANNELS["REPORTS"] = 1235095919788167269
        LOG_CHANNELS["GATE"] = 1235095919788167269
        LOG_CHANNELS["DEV"] = 1235095919788167269
        LOG_CHANNELS["PRIVATE"] = 1235095919788167269

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
        # # tux feet yellow
        "DEFAULT": 0xF4D01A,
        # # tux feet yellow
        "LOG": 0xF4D01A,
        # # catppuccin mocha sky
        "INFO": 0x89DCEB,
        # # catppuccin latte peach
        "WARNING": 0xFE640B,
        # # catppuccin latte red
        "ERROR": 0xD20F39,
        # # catppuccin mocha green
        "SUCCESS": 0xA6E3A1,
        # # catppuccin mocha mauve
        "DEBUG": 0xCBA6F7,
        # # pure black
        # "BLACK": 0x000000,
        # # pure white
        # "WHITE": 0xFFFFFF,
        # # catppuccin yellow
        "POLL": 0xF9E2AF,
        # # catppuccin crust
        "INFRACTION": 0x11111B,
        #######################
        # TOKYO NIGHT COLORS
        "FOREGROUND": 0xA9B1DC,
        "BACKGROUND": 0x1A1B2C,
        "BLACK": 0x414868,
        "CURSOR": 0xC0CAF5,
        "SELECT": 0x28344A,
        "RED": 0xF7768E,
        "GREEN": 0x73DACA,
        "YELLOW": 0xE0AF68,
        "BLUE": 0x7AA2F7,
        "PURPLE": 0xBB9AF7,
        "CYAN": 0x7DCFFF,
        "WHITE": 0xC0CAF5,
    }

    EMBED_STATE_ICONS: Final[dict[str, str]] = {
        "DEFAULT": "https://i.imgur.com/EqzIMKr.png",
        "LOG": "https://i.imgur.com/4sblrd0.png",
        "INFO": "https://github.com/catppuccin/catppuccin/blob/main/assets/palette/circles/mocha_sky.png?raw=true",
        "WARNING": "https://github.com/catppuccin/catppuccin/raw/main/assets/palette/circles/latte_peach.png?raw=true",
        "ERROR": "https://github.com/catppuccin/catppuccin/blob/main/assets/palette/circles/latte_red.png?raw=true",
        "SUCCESS": "https://github.com/catppuccin/catppuccin/blob/main/assets/palette/circles/mocha_green.png?raw=true",
        "POLL": "https://github.com/catppuccin/catppuccin/raw/main/assets/palette/circles/mocha_yellow.png?raw=true",
        "INFRACTION": "https://github.com/catppuccin/catppuccin/raw/main/assets/palette/circles/mocha_crust.png?raw=true",
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
