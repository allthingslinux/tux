import base64
import os
from pathlib import Path
from typing import Any, Final, cast

import yaml
from dotenv import load_dotenv
from loguru import logger
from tux import __version__ as app_version
from utils.env import get_bot_token, get_database_url, is_dev_mode


def convert_dict_str_to_int(original_dict: dict[str, int]) -> dict[int, int]:
    """Convert a dictionary with string keys to one with integer keys.

    Parameters
    ----------
    original_dict : dict[str, int]
        The original dictionary with string keys.

    Returns
    -------
    dict[int, int]
        The new dictionary with integer keys.
    """
    return {int(k): v for k, v in original_dict.items()}


# Load environment variables from .env file
load_dotenv(verbose=True)

# Get the workspace root directory
workspace_root = Path(__file__).parent.parent.parent

config_file = workspace_root / "config/settings.yml"
config_file_example = workspace_root / "config/settings.yml.example"
config = yaml.safe_load(config_file.read_text())
config_example = yaml.safe_load(config_file_example.read_text())


# Recursively merge defaults into user config (fills nested missing keys too)
def merge_defaults(user: dict[str, Any], default: dict[str, Any]) -> None:
    for key, default_val in default.items():
        if key not in user:
            user[key] = default_val
            logger.warning(f"Added missing config key: {key}")
        elif isinstance(default_val, dict) and isinstance(user.get(key), dict):
            merge_defaults(user[key], cast(dict[str, Any], default_val))


merge_defaults(config, config_example)


class Config:
    # Permissions
    BOT_OWNER_ID: Final[int] = config["USER_IDS"]["BOT_OWNER"]
    SYSADMIN_IDS: Final[list[int]] = config["USER_IDS"]["SYSADMINS"]
    ALLOW_SYSADMINS_EVAL: Final[bool] = config["ALLOW_SYSADMINS_EVAL"]

    # Production env
    DEFAULT_PROD_PREFIX: Final[str] = config["BOT_INFO"]["PROD_PREFIX"]
    PROD_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("PROD_COG_IGNORE_LIST", "").split(","))

    # Dev env
    DEFAULT_DEV_PREFIX: Final[str] = config["BOT_INFO"]["DEV_PREFIX"]
    DEV_COG_IGNORE_LIST: Final[set[str]] = set(os.getenv("DEV_COG_IGNORE_LIST", "").split(","))

    # Bot info
    BOT_NAME: Final[str] = config["BOT_INFO"]["BOT_NAME"]
    BOT_VERSION: Final[str] = app_version or "0.0.0"
    ACTIVITIES: Final[str] = config["BOT_INFO"]["ACTIVITIES"]
    HIDE_BOT_OWNER: Final[bool] = config["BOT_INFO"]["HIDE_BOT_OWNER"]

    # Status Roles
    STATUS_ROLES: Final[list[dict[str, int]]] = config["STATUS_ROLES"]

    # Debug env
    DEBUG: Final[bool] = bool(os.getenv("DEBUG", "True"))

    # Final env - use the env module to determine development vs production
    DEFAULT_PREFIX: Final[str] = DEFAULT_DEV_PREFIX if is_dev_mode() else DEFAULT_PROD_PREFIX
    COG_IGNORE_LIST: Final[set[str]] = DEV_COG_IGNORE_LIST if is_dev_mode() else PROD_COG_IGNORE_LIST

    # Sentry-related
    SENTRY_DSN: Final[str | None] = os.getenv("SENTRY_DSN", "")

    # Database - use the env module to get the appropriate URL
    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        """Get the database URL for the current environment."""
        # The environment mode is assumed to be set by the CLI entry point
        # before this property is accessed.
        return get_database_url()  # Get URL based on manager's current env

    # Bot Token - use the env module to get the appropriate token
    @property
    def BOT_TOKEN(self) -> str:  # noqa: N802
        """Get the bot token for the current environment."""
        # The environment mode is assumed to be set by the CLI entry point
        # before this property is accessed.
        return get_bot_token()  # Get token based on manager's current env

    # Wolfram
    WOLFRAM_APP_ID: Final[str] = os.getenv("WOLFRAM_APP_ID", "")

    # InfluxDB
    INFLUXDB_TOKEN: Final[str] = os.getenv("INFLUXDB_TOKEN", "")
    INFLUXDB_URL: Final[str] = os.getenv("INFLUXDB_URL", "")
    INFLUXDB_ORG: Final[str] = os.getenv("INFLUXDB_ORG", "")

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
