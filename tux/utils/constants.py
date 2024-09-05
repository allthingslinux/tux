import base64
import os
from pathlib import Path
from typing import Final

import yaml
from dotenv import load_dotenv, set_key

load_dotenv(verbose=True)

config_file = Path("config/settings.yml")
config = yaml.safe_load(config_file.read_text())


class Constants:
    # Permission constants
    BOT_OWNER_ID: Final[int] = config["USER_IDS"]["BOT_OWNER"]
    SYSADMIN_IDS: Final[list[int]] = config["USER_IDS"]["SYSADMINS"]

    # Production env constants
    PROD_TOKEN: Final[str] = os.getenv("PROD_TOKEN", "")
    DEFAULT_PROD_PREFIX: Final[str] = config["DEFAULT_PREFIX"]["PROD"]
    PROD_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("PROD_COG_IGNORE_LIST", "").split(","))

    # Dev env constants
    DEV: Final[str | None] = os.getenv("DEV")
    DEV_TOKEN: Final[str] = os.getenv("DEV_TOKEN", "")
    DEFAULT_DEV_PREFIX: Final[str] = config["DEFAULT_PREFIX"]["DEV"]
    DEV_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("DEV_COG_IGNORE_LIST", "").split(","))

    # Debug env constants
    DEBUG: Final[bool] = bool(os.getenv("DEBUG", "True"))

    # Final env constants
    TOKEN: Final[str] = DEV_TOKEN if DEV and DEV.lower() == "true" else PROD_TOKEN
    DEFAULT_PREFIX: Final[str] = DEFAULT_DEV_PREFIX if DEV and DEV.lower() == "true" else DEFAULT_PROD_PREFIX
    COG_IGNORE_LIST: Final[set[str]] = DEV_COG_IGNORE_LIST if DEV and DEV.lower() == "true" else PROD_COG_IGNORE_LIST

    # Sentry-related constants
    SENTRY_URL: Final[str | None] = os.getenv("SENTRY_URL", "")

    # Database constants
    PROD_DATABASE_URL: Final[str] = os.getenv("PROD_DATABASE_URL", "")
    DEV_DATABASE_URL: Final[str] = os.getenv("DEV_DATABASE_URL", "")

    DATABASE_URL: Final[str] = DEV_DATABASE_URL if DEV and DEV.lower() == "true" else PROD_DATABASE_URL

    set_key(".env", "DATABASE_URL", DATABASE_URL)

    # GitHub constants
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

    # Mailcow constants
    MAILCOW_API_KEY: Final[str] = os.getenv("MAILCOW_API_KEY", "")
    MAILCOW_API_URL: Final[str] = os.getenv("MAILCOW_API_URL", "")

    # Temp VC constants
    TEMPVC_CATEGORY_ID: Final[str | None] = config["TEMPVC_CATEGORY_ID"]
    TEMPVC_CHANNEL_ID: Final[str | None] = config["TEMPVC_CHANNEL_ID"]

    # Color constants
    EMBED_COLORS: Final[dict[str, int]] = config["EMBED_COLORS"]

    # Icon constants
    EMBED_ICONS: Final[dict[str, str]] = config["EMBED_ICONS"]

    # Embed limit constants
    EMBED_MAX_NAME_LENGTH = 256
    EMBED_MAX_DESC_LENGTH = 4096
    EMBED_MAX_FIELDS = 25
    EMBED_TOTAL_MAX = 6000
    EMBED_FIELD_VALUE_LENGTH = 1024

    NICKNAME_MAX_LENGTH = 32

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


CONST = Constants()
