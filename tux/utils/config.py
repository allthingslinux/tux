import base64
import os
from pathlib import Path
from typing import ClassVar, Final

import yaml
from dotenv import load_dotenv, set_key

# Load shared environment variables from .env
load_dotenv(dotenv_path=".env")

# Determine which environment file to load based on TUX_ENV
env = os.getenv("TUX_ENV", "dev").lower()

# Load the environment-specific .env file
env_file = ".env.prod" if env == "prod" else ".env.dev"
load_dotenv(dotenv_path=env_file)

# Load YAML configuration
settings_file_path = Path("config/settings.yml")
settings = yaml.safe_load(settings_file_path.read_text())


class Config:
    # Environment-specific constants
    TUX_ENV: Final[str] = os.getenv("TUX_ENV", "dev")
    TUX_TOKEN: Final[str] = os.getenv("TUX_TOKEN", "")

    POSTGRES_PASSWORD: Final[str] = os.getenv("POSTGRES_PASSWORD", "tux")
    POSTGRES_PORT: Final[str] = os.getenv("POSTGRES_PORT", "5432")

    # Derived settings
    DATABASE_URL: Final[str] = f"postgresql://postgres:{POSTGRES_PASSWORD}@db:{POSTGRES_PORT}/postgres"

    set_key(".env", "DATABASE_URL", DATABASE_URL)

    # Cog ignore list constants
    COG_IGNORE_LIST: ClassVar[set[str]] = set(os.getenv("COG_IGNORE_LIST", "").split(","))

    # Sentry constants
    SENTRY_URL: Final[str] = os.getenv("SENTRY_URL", "")

    # Default command prefixes based on TUX_ENV
    DEFAULT_PREFIX: Final[str] = (
        settings["DEFAULT_PREFIX"]["DEV"] if TUX_ENV == "dev" else settings["DEFAULT_PREFIX"]["PROD"]
    )

    # Non-environment-specific GitHub constants
    GITHUB_REPO_URL: Final[str] = os.getenv("GITHUB_REPO_URL", "")
    GITHUB_REPO_OWNER: Final[str] = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO: Final[str] = os.getenv("GITHUB_REPO", "")
    GITHUB_TOKEN: Final[str] = os.getenv("GITHUB_TOKEN", "")
    GITHUB_APP_ID: Final[int] = int(os.getenv("GITHUB_APP_ID", "0"))
    GITHUB_CLIENT_ID: Final[str] = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: Final[str] = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_PUBLIC_KEY: Final[str] = os.getenv("GITHUB_PUBLIC_KEY", "")
    GITHUB_INSTALLATION_ID: Final[str] = os.getenv("GITHUB_INSTALLATION_ID", "0")
    GITHUB_PRIVATE_KEY: Final[str] = (
        base64.b64decode(os.getenv("GITHUB_PRIVATE_KEY_BASE64", "")).decode("utf-8")
        if os.getenv("GITHUB_PRIVATE_KEY_BASE64")
        else ""
    )

    # Non-environment-specific Mailcow constants
    MAILCOW_API_KEY: Final[str] = os.getenv("MAILCOW_API_KEY", "")
    MAILCOW_API_URL: Final[str] = os.getenv("MAILCOW_API_URL", "")

    # Permission constants via config/settings.yml
    BOT_OWNER_ID: Final[int] = settings["USER_IDS"]["BOT_OWNER"]
    SYSADMIN_IDS: Final[list[int]] = settings["USER_IDS"]["SYSADMINS"]

    # Temp VC constants via config/settings.yml
    TEMPVC_CATEGORY_ID: Final[str | None] = settings["TEMPVC_CATEGORY_ID"]
    TEMPVC_CHANNEL_ID: Final[str | None] = settings["TEMPVC_CHANNEL_ID"]


CONFIG = Config()
