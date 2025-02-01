import base64
import os
from pathlib import Path
from typing import Final

import yaml
from dotenv import load_dotenv, set_key

from tux.utils.functions import convert_dict_str_to_int

load_dotenv(verbose=True)

config_file = Path("config/settings.yml")
config = yaml.safe_load(config_file.read_text())


class Config:
    # Permissions
    BOT_OWNER_ID: Final[int] = config["USER_IDS"]["BOT_OWNER"]
    SYSADMIN_IDS: Final[list[int]] = config["USER_IDS"]["SYSADMINS"]

    # Production env
    PROD_TOKEN: Final[str] = os.getenv("PROD_TOKEN", "")
    DEFAULT_PROD_PREFIX: Final[str] = config["BOT_INFO"]["PROD_PREFIX"]
    PROD_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("PROD_COG_IGNORE_LIST", "").split(","))

    # Dev env
    DEV: Final[str | None] = os.getenv("DEV")
    DEV_TOKEN: Final[str] = os.getenv("DEV_TOKEN", "")
    DEFAULT_DEV_PREFIX: Final[str] = config["BOT_INFO"]["DEV_PREFIX"]
    DEV_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("DEV_COG_IGNORE_LIST", "").split(","))

    # Bot info
    BOT_NAME: Final[str] = config["BOT_INFO"]["BOT_NAME"]
    BOT_VERSION: Final[str] = config["BOT_INFO"]["BOT_VERSION"]
    ACTIVITIES: Final[str] = config["BOT_INFO"]["ACTIVITIES"]

    # Debug env
    DEBUG: Final[bool] = bool(os.getenv("DEBUG", "True"))

    # Final env
    TOKEN: Final[str] = DEV_TOKEN if DEV and DEV.lower() == "true" else PROD_TOKEN
    DEFAULT_PREFIX: Final[str] = DEFAULT_DEV_PREFIX if DEV and DEV.lower() == "true" else DEFAULT_PROD_PREFIX
    COG_IGNORE_LIST: Final[set[str]] = DEV_COG_IGNORE_LIST if DEV and DEV.lower() == "true" else PROD_COG_IGNORE_LIST

    # Sentry-related
    SENTRY_URL: Final[str | None] = os.getenv("SENTRY_URL", "")

    # Database
    PROD_DATABASE_URL: Final[str] = os.getenv("PROD_DATABASE_URL", "")
    DEV_DATABASE_URL: Final[str] = os.getenv("DEV_DATABASE_URL", "")

    DATABASE_URL: Final[str] = DEV_DATABASE_URL if DEV and DEV.lower() == "true" else PROD_DATABASE_URL

    set_key(".env", "DATABASE_URL", DATABASE_URL)

    # GitHub
    GITHUB_REPO_URL: Final[str] = os.getenv("GITHUB_REPO_URL", "")
    GITHUB_REPO_OWNER: Final[str] = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO: Final[str] = os.getenv("GITHUB_REPO", "")
    GITHUB_TOKEN: Final[str] = os.getenv("GITHUB_TOKEN", "")
    GITHUB_APP_ID: Final[int] = int(os.getenv("GITHUB_APP_ID") or "0")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_PUBLIC_KEY = os.getenv("GITHUB_PUBLIC_KEY", "")
    GITHUB_INSTALLATION_ID: Final[str] = os.getenv("GITHUB_INSTALLATION_ID") or "0"
    GITHUB_PRIVATE_KEY: str = (
        base64.b64decode(os.getenv("GITHUB_PRIVATE_KEY_BASE64", "")).decode("utf-8")
        if os.getenv("GITHUB_PRIVATE_KEY_BASE64")
        else ""
    )

    # Mailcow
    MAILCOW_API_KEY: Final[str] = os.getenv("MAILCOW_API_KEY", "")
    MAILCOW_API_URL: Final[str] = os.getenv("MAILCOW_API_URL", "")

    # Temp VC
    TEMPVC_CATEGORY_ID: Final[str | None] = config["TEMPVC_CATEGORY_ID"]
    TEMPVC_CHANNEL_ID: Final[str | None] = config["TEMPVC_CHANNEL_ID"]

    # GIF ratelimiter
    RECENT_GIF_AGE: Final[int] = config["GIF_LIMITER"]["RECENT_GIF_AGE"]
    GIF_LIMIT_EXCLUDE: Final[list[int]] = config["GIF_LIMITER"]["GIF_LIMIT_EXCLUDE"]

    GIF_LIMITS: Final[dict[int, int]] = convert_dict_str_to_int(config["GIF_LIMITER"]["GIF_LIMITS_USER"])
    GIF_LIMITS_CHANNEL: Final[dict[int, int]] = convert_dict_str_to_int(config["GIF_LIMITER"]["GIF_LIMITS_CHANNEL"])

    XP_BLACKLIST_CHANNELS: Final[list[int]] = config["XP"]["XP_BLACKLIST_CHANNELS"]
    XP_ROLES: Final[list[dict[str, int]]] = config["XP"]["XP_ROLES"]
    XP_MULTIPLIERS: Final[list[dict[str, int | float]]] = config["XP"]["XP_MULTIPLIERS"]
    XP_COOLDOWN: Final[int] = config["XP"]["XP_COOLDOWN"]
    LEVELS_EXPONENT: Final[int] = config["XP"]["LEVELS_EXPONENT"]
    SHOW_XP_PROGRESS: Final[bool] = config["XP"].get("SHOW_XP_PROGRESS", False)
    ENABLE_XP_CAP: Final[bool] = config["XP"].get("ENABLE_XP_CAP", True)

    # Snippet stuff
    LIMIT_TO_ROLE_IDS: Final[bool] = config["SNIPPETS"]["LIMIT_TO_ROLE_IDS"]
    ACCESS_ROLE_IDS: Final[list[int]] = config["SNIPPETS"]["ACCESS_ROLE_IDS"]


CONFIG = Config()
