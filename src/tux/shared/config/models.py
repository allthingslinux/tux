"""Pydantic configuration models for Tux.

This module contains all the Pydantic models for configuration,
extracted from the existing config.py file for better organization.
"""

from typing import Annotated, Any

from pydantic import BaseModel, Field


class BotInfo(BaseModel):
    """Bot information configuration."""

    BOT_NAME: Annotated[
        str,
        Field(
            default="Tux",
            description="Name of the bot",
            examples=["Tux", "MyBot"],
        ),
    ]
    ACTIVITIES: Annotated[
        str,
        Field(
            default="[]",
            description="Bot activities",
            examples=[
                '[{"type": 0, "name": "with Linux"}]',
                '[{"type": 2, "name": "to commands", "url": "https://twitch.tv/example"}]',
            ],
        ),
    ]
    HIDE_BOT_OWNER: Annotated[
        bool,
        Field(
            default=False,
            description="Hide bot owner info",
            examples=[False, True],
        ),
    ]
    PREFIX: Annotated[
        str,
        Field(
            default="$",
            description="Command prefix",
            examples=["$", "!", "tux.", "?"],
        ),
    ]


class UserIds(BaseModel):
    """User ID configuration."""

    BOT_OWNER_ID: Annotated[
        int,
        Field(
            default=0,
            description="Bot owner user ID",
            examples=[123456789012345678],
        ),
    ]
    SYSADMINS: Annotated[
        list[int],
        Field(
            default_factory=list,
            description="System admin user IDs",
            examples=[[123456789012345678, 987654321098765432]],
        ),
    ]


class StatusRoles(BaseModel):
    """Status roles configuration."""

    MAPPINGS: Annotated[
        list[dict[str, Any]],
        Field(
            default_factory=list,
            description="Status to role mappings",
            examples=[[{"status": ".gg/linux", "role_id": 123456789012345678}]],
        ),
    ]


class TempVC(BaseModel):
    """Temporary voice channel configuration."""

    TEMPVC_CHANNEL_ID: Annotated[
        str | None,
        Field(
            default=None,
            description="Temporary VC channel ID",
            examples=["123456789012345678"],
        ),
    ]
    TEMPVC_CATEGORY_ID: Annotated[
        str | None,
        Field(
            default=None,
            description="Temporary VC category ID",
            examples=["123456789012345678"],
        ),
    ]


class GifLimiter(BaseModel):
    """GIF limiter configuration."""

    RECENT_GIF_AGE: Annotated[
        int,
        Field(
            default=60,
            description="Recent GIF age limit",
            examples=[60, 120, 300],
        ),
    ]
    GIF_LIMITS_USER: Annotated[
        dict[int, int],
        Field(
            default_factory=dict,
            description="User GIF limits",
            examples=[{"123456789012345678": 5}],
        ),
    ]
    GIF_LIMITS_CHANNEL: Annotated[
        dict[int, int],
        Field(
            default_factory=dict,
            description="Channel GIF limits",
            examples=[{"123456789012345678": 10}],
        ),
    ]
    GIF_LIMIT_EXCLUDE: Annotated[
        list[int],
        Field(
            default_factory=list,
            description="Excluded channels",
            examples=[[123456789012345678]],
        ),
    ]


class XP(BaseModel):
    """XP system configuration."""

    XP_BLACKLIST_CHANNELS: Annotated[
        list[int],
        Field(
            default_factory=list,
            description="XP blacklist channels",
            examples=[[123456789012345678]],
        ),
    ]
    XP_ROLES: Annotated[
        list[dict[str, int]],
        Field(
            default_factory=list,
            description="XP roles",
            examples=[[{"role_id": 123456789012345678, "xp_required": 1000}]],
        ),
    ]
    XP_MULTIPLIERS: Annotated[
        list[dict[str, int | float]],
        Field(
            default_factory=list,
            description="XP multipliers",
            examples=[[{"role_id": 123456789012345678, "multiplier": 1.5}]],
        ),
    ]
    XP_COOLDOWN: Annotated[
        int,
        Field(
            default=1,
            description="XP cooldown in seconds",
            examples=[1, 5, 10],
        ),
    ]
    LEVELS_EXPONENT: Annotated[
        int,
        Field(
            default=2,
            description="Levels exponent",
            examples=[2, 3, 1.5],
        ),
    ]
    SHOW_XP_PROGRESS: Annotated[
        bool,
        Field(
            default=True,
            description="Show XP progress",
            examples=[True, False],
        ),
    ]
    ENABLE_XP_CAP: Annotated[
        bool,
        Field(
            default=False,
            description="Enable XP cap",
            examples=[False, True],
        ),
    ]


class Snippets(BaseModel):
    """Snippets configuration."""

    LIMIT_TO_ROLE_IDS: Annotated[
        bool,
        Field(
            default=False,
            description="Limit snippets to specific roles",
            examples=[False, True],
        ),
    ]
    ACCESS_ROLE_IDS: Annotated[
        list[int],
        Field(
            default_factory=list,
            description="Snippet access role IDs",
            examples=[[123456789012345678, 987654321098765432]],
        ),
    ]


class IRC(BaseModel):
    """IRC bridge configuration."""

    BRIDGE_WEBHOOK_IDS: Annotated[
        list[int],
        Field(
            default_factory=list,
            description="IRC bridge webhook IDs",
            examples=[[123456789012345678]],
        ),
    ]


class ExternalServices(BaseModel):
    """External services configuration."""

    SENTRY_DSN: Annotated[
        str,
        Field(
            default="",
            description="Sentry DSN",
            examples=["https://key@o123456.ingest.sentry.io/123456"],
        ),
    ]
    GITHUB_APP_ID: Annotated[
        str,
        Field(
            default="",
            description="GitHub app ID",
            examples=["123456"],
        ),
    ]
    GITHUB_INSTALLATION_ID: Annotated[
        str,
        Field(
            default="",
            description="GitHub installation ID",
            examples=["12345678"],
        ),
    ]
    GITHUB_PRIVATE_KEY: Annotated[
        str,
        Field(
            default="",
            description="GitHub private key",
            examples=["-----BEGIN RSA PRIVATE KEY-----\n..."],
        ),
    ]
    GITHUB_CLIENT_ID: Annotated[
        str,
        Field(
            default="",
            description="GitHub client ID",
            examples=["Iv1.1234567890abcdef"],
        ),
    ]
    GITHUB_CLIENT_SECRET: Annotated[
        str,
        Field(
            default="",
            description="GitHub client secret",
            examples=["1234567890abcdef1234567890abcdef12345678"],
        ),
    ]
    GITHUB_REPO_URL: Annotated[
        str,
        Field(
            default="",
            description="GitHub repository URL",
            examples=["https://github.com/owner/repo"],
        ),
    ]
    GITHUB_REPO_OWNER: Annotated[
        str,
        Field(
            default="",
            description="GitHub repository owner",
            examples=["owner"],
        ),
    ]
    GITHUB_REPO: Annotated[
        str,
        Field(
            default="",
            description="GitHub repository name",
            examples=["repo"],
        ),
    ]
    MAILCOW_API_KEY: Annotated[
        str,
        Field(
            default="",
            description="Mailcow API key",
            examples=["abc123def456ghi789"],
        ),
    ]
    MAILCOW_API_URL: Annotated[
        str,
        Field(
            default="",
            description="Mailcow API URL",
            examples=["https://mail.example.com/api/v1"],
        ),
    ]
    WOLFRAM_APP_ID: Annotated[
        str,
        Field(
            default="",
            description="Wolfram Alpha app ID",
            examples=["ABC123-DEF456GHI789"],
        ),
    ]
    INFLUXDB_TOKEN: Annotated[
        str,
        Field(
            default="",
            description="InfluxDB token",
            examples=["abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"],
        ),
    ]
    INFLUXDB_URL: Annotated[
        str,
        Field(
            default="",
            description="InfluxDB URL",
            examples=["https://us-east-1-1.aws.cloud2.influxdata.com"],
        ),
    ]
    INFLUXDB_ORG: Annotated[
        str,
        Field(
            default="",
            description="InfluxDB organization",
            examples=["my-org"],
        ),
    ]


class DatabaseConfig(BaseModel):
    """Database configuration with automatic URL construction."""

    # Individual database credentials (standard PostgreSQL env vars)
    POSTGRES_HOST: Annotated[
        str,
        Field(
            default="localhost",
            description="PostgreSQL host",
            examples=["localhost", "tux-postgres", "db.example.com"],
        ),
    ]
    POSTGRES_PORT: Annotated[
        int,
        Field(
            default=5432,
            description="PostgreSQL port",
            examples=[5432, 5433],
        ),
    ]
    POSTGRES_DB: Annotated[
        str,
        Field(
            default="tuxdb",
            description="PostgreSQL database name",
            examples=["tuxdb", "tux_production"],
        ),
    ]
    POSTGRES_USER: Annotated[
        str,
        Field(
            default="tuxuser",
            description="PostgreSQL username",
            examples=["tuxuser", "tux_admin"],
        ),
    ]
    POSTGRES_PASSWORD: Annotated[
        str,
        Field(
            default="tuxpass",
            description="PostgreSQL password",
            examples=["ChangeThisToAStrongPassword123!", "SecurePassword456!"],
        ),
    ]

    # Custom database URL override (optional)
    DATABASE_URL: Annotated[
        str,
        Field(
            default="",
            description="Custom database URL override",
            examples=[
                "postgresql://user:password@localhost:5432/tuxdb",
                "postgresql+psycopg://user:pass@host:5432/db",
            ],
        ),
    ]

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
