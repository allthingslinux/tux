"""Pydantic configuration models for Tux.

This module contains all the Pydantic models for configuration,
extracted from the existing config.py file for better organization.
"""

from typing import Any

from pydantic import BaseModel, Field


class BotInfo(BaseModel):
    """Bot information configuration."""

    BOT_NAME: str = Field(default="Tux", description="Name of the bot")
    ACTIVITIES: str = Field(default="[]", description="Bot activities")
    HIDE_BOT_OWNER: bool = Field(default=False, description="Hide bot owner info")
    PREFIX: str = Field(default="$", description="Command prefix")


class UserIds(BaseModel):
    """User ID configuration."""

    BOT_OWNER_ID: int = Field(default=0, description="Bot owner user ID")
    SYSADMINS: list[int] = Field(default_factory=list, description="System admin user IDs")


class StatusRoles(BaseModel):
    """Status roles configuration."""

    MAPPINGS: list[dict[str, Any]] = Field(default_factory=list, description="Status to role mappings")


class TempVC(BaseModel):
    """Temporary voice channel configuration."""

    TEMPVC_CHANNEL_ID: str | None = Field(default=None, description="Temporary VC channel ID")
    TEMPVC_CATEGORY_ID: str | None = Field(default=None, description="Temporary VC category ID")


class GifLimiter(BaseModel):
    """GIF limiter configuration."""

    RECENT_GIF_AGE: int = Field(default=60, description="Recent GIF age limit")
    GIF_LIMITS_USER: dict[int, int] = Field(default_factory=dict, description="User GIF limits")
    GIF_LIMITS_CHANNEL: dict[int, int] = Field(default_factory=dict, description="Channel GIF limits")
    GIF_LIMIT_EXCLUDE: list[int] = Field(default_factory=list, description="Excluded channels")


class XP(BaseModel):
    """XP system configuration."""

    XP_BLACKLIST_CHANNELS: list[int] = Field(default_factory=list, description="XP blacklist channels")
    XP_ROLES: list[dict[str, int]] = Field(default_factory=list, description="XP roles")
    XP_MULTIPLIERS: list[dict[str, int | float]] = Field(default_factory=list, description="XP multipliers")
    XP_COOLDOWN: int = Field(default=1, description="XP cooldown in seconds")
    LEVELS_EXPONENT: int = Field(default=2, description="Levels exponent")
    SHOW_XP_PROGRESS: bool = Field(default=True, description="Show XP progress")
    ENABLE_XP_CAP: bool = Field(default=False, description="Enable XP cap")


class Snippets(BaseModel):
    """Snippets configuration."""

    LIMIT_TO_ROLE_IDS: bool = Field(default=False, description="Limit snippets to specific roles")
    ACCESS_ROLE_IDS: list[int] = Field(default_factory=list, description="Snippet access role IDs")


class IRC(BaseModel):
    """IRC bridge configuration."""

    BRIDGE_WEBHOOK_IDS: list[int] = Field(default_factory=list, description="IRC bridge webhook IDs")


class ExternalServices(BaseModel):
    """External services configuration."""

    SENTRY_DSN: str = Field(default="", description="Sentry DSN")
    GITHUB_APP_ID: str = Field(default="", description="GitHub app ID")
    GITHUB_INSTALLATION_ID: str = Field(default="", description="GitHub installation ID")
    GITHUB_PRIVATE_KEY: str = Field(default="", description="GitHub private key")
    GITHUB_CLIENT_ID: str = Field(default="", description="GitHub client ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", description="GitHub client secret")
    GITHUB_REPO_URL: str = Field(default="", description="GitHub repository URL")
    GITHUB_REPO_OWNER: str = Field(default="", description="GitHub repository owner")
    GITHUB_REPO: str = Field(default="", description="GitHub repository name")
    MAILCOW_API_KEY: str = Field(default="", description="Mailcow API key")
    MAILCOW_API_URL: str = Field(default="", description="Mailcow API URL")
    WOLFRAM_APP_ID: str = Field(default="", description="Wolfram Alpha app ID")
    INFLUXDB_TOKEN: str = Field(default="", description="InfluxDB token")
    INFLUXDB_URL: str = Field(default="", description="InfluxDB URL")
    INFLUXDB_ORG: str = Field(default="", description="InfluxDB organization")


class DatabaseConfig(BaseModel):
    """Database configuration with automatic URL construction."""

    # Individual database credentials (standard PostgreSQL env vars)
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="tuxdb", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="tuxuser", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="tuxpass", description="PostgreSQL password")

    # Custom database URL override (optional)
    DATABASE_URL: str = Field(default="", description="Custom database URL override")

    def get_database_url(self) -> str:
        """Get database URL, either custom or constructed from individual parts.

        Returns
        -------
        str
            Complete PostgreSQL database URL.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # Construct from individual parts
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
