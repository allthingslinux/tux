"""Main Tux configuration using Pydantic Settings.

This module provides the main configuration class and global instance,
using the extracted models and proper pydantic-settings for environment variable binding.

Configuration loading priority (highest to lowest):
1. Environment variables
2. .env file
3. config/config.toml or config.toml file
4. config/config.yaml or config.yaml file
5. config/config.json or config.json file
6. Default values
"""

import base64
import os
import warnings
from pathlib import Path
from typing import Annotated

from pydantic import Field, computed_field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from tux.shared.constants import ENCODING_UTF8

from .loaders import JsonConfigSource, TomlConfigSource, YamlConfigSource
from .models import (
    IRC,
    XP,
    BotInfo,
    ExternalServices,
    GifLimiter,
    Snippets,
    StatusRoles,
    TempVC,
    UserIds,
)


def validate_environment() -> None:
    """
    Validate critical environment variables for security and correctness.

    Raises
    ------
    ValueError
        If an insecure default password is used.
    """
    # Check database password strength - exclude known Docker passwords
    db_password = os.getenv("POSTGRES_PASSWORD", "")
    weak_passwords = ["password", "admin", "postgres", "123456", "qwerty"]

    # Only warn for truly weak passwords, not the Docker default
    if db_password and db_password in weak_passwords:
        warnings.warn(
            "⚠️  SECURITY WARNING: Using weak/default database password! Please set a strong POSTGRES_PASSWORD.",
            UserWarning,
            stacklevel=2,
        )

    # Don't enforce length requirement for Docker default password
    if (
        db_password
        and len(db_password) < 12
        and db_password not in ["ChangeThisToAStrongPassword123!"]
    ):
        warnings.warn(
            "⚠️  SECURITY WARNING: Database password is very short (<12 chars). "
            "Use a longer password for better security.",
            UserWarning,
            stacklevel=2,
        )

    # Only block truly insecure default passwords
    if db_password in ["tuxpass", "password", "admin", "postgres"]:
        error_msg = (
            f"❌ SECURITY ERROR: Cannot use insecure password '{db_password}'! "
            "Please set a strong POSTGRES_PASSWORD environment variable."
        )
        raise ValueError(error_msg)


# Validate environment when module is imported
validate_environment()


class Config(BaseSettings):
    """Main Tux configuration using Pydantic Settings with multi-format support.

    Configuration is loaded from multiple sources in priority order:
    1. Environment variables (highest priority)
    2. .env file
    3. config/config.toml or config.toml file
    4. config/config.yaml or config.yaml file
    5. config/config.json or config.json file
    6. Default values (lowest priority)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding=ENCODING_UTF8,
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Core configuration
    DEBUG: Annotated[
        bool,
        Field(
            default=False,
            description="Enable debug mode",
            examples=[False, True],
        ),
    ]
    LOG_LEVEL: Annotated[
        str,
        Field(
            default="INFO",
            description="Logging level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)",
            examples=["INFO", "DEBUG", "WARNING", "ERROR"],
        ),
    ]

    # Bot tokens
    BOT_TOKEN: Annotated[
        str,
        Field(
            default="",
            description="Discord bot token",
            examples=[
                "FakeDiscordBotTokenBecauseGitHubSecurityIsAnnoying",
            ],
        ),
    ]

    # Database configuration (standard PostgreSQL env vars)
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
            default="ChangeThisToAStrongPassword123!",
            description="PostgreSQL password",
            examples=["ChangeThisToAStrongPassword123!", "SecurePassword456!"],
        ),
    ]

    # Optional: Custom database URL override
    DATABASE_URL: Annotated[
        str,
        Field(
            default="",
            description="Custom database URL override",
            examples=["postgresql://user:password@localhost:5432/tuxdb"],
        ),
    ]

    # Bot info
    BOT_INFO: BotInfo = Field(default_factory=BotInfo)  # type: ignore[arg-type]

    # User permissions
    USER_IDS: UserIds = Field(default_factory=UserIds)  # type: ignore[arg-type]
    ALLOW_SYSADMINS_EVAL: Annotated[
        bool,
        Field(
            default=False,
            description="Allow sysadmins to use eval",
            examples=[False, True],
        ),
    ]

    # Features
    STATUS_ROLES: StatusRoles = Field(default_factory=StatusRoles)  # type: ignore[arg-type]
    TEMPVC: TempVC = Field(default_factory=TempVC)  # type: ignore[arg-type]
    GIF_LIMITER: GifLimiter = Field(default_factory=GifLimiter)  # type: ignore[arg-type]
    XP_CONFIG: XP = Field(default_factory=XP)  # type: ignore[arg-type]
    SNIPPETS: Snippets = Field(default_factory=Snippets)  # type: ignore[arg-type]
    IRC_CONFIG: IRC = Field(default_factory=IRC)  # type: ignore[arg-type]

    # External services
    EXTERNAL_SERVICES: ExternalServices = Field(default_factory=ExternalServices)  # type: ignore[arg-type]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to load from multiple file formats.

        Priority order (highest to lowest):
        1. Init settings (programmatic overrides)
        2. Environment variables
        3. .env file
        4. config.toml file
        5. config.yaml file
        6. config.json file
        7. File secret settings (Docker secrets, etc.)

        Parameters
        ----------
        settings_cls : type[BaseSettings]
            The settings class
        init_settings : PydanticBaseSettingsSource
            Init settings source
        env_settings : PydanticBaseSettingsSource
            Environment settings source
        dotenv_settings : PydanticBaseSettingsSource
            .env file settings source
        file_secret_settings : PydanticBaseSettingsSource
            File secret settings source

        Returns
        -------
        tuple[PydanticBaseSettingsSource, ...]
            Tuple of settings sources in priority order

        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            # TOML sources (config/config.toml takes priority over root config.toml)
            TomlConfigSource(settings_cls, Path("config/config.toml")),
            TomlConfigSource(settings_cls, Path("config.toml")),
            # YAML sources
            YamlConfigSource(settings_cls, Path("config/config.yaml")),
            YamlConfigSource(settings_cls, Path("config.yaml")),
            # JSON sources
            JsonConfigSource(settings_cls, Path("config/config.json")),
            JsonConfigSource(settings_cls, Path("config.json")),
            file_secret_settings,
        )

    @computed_field
    @property
    def database_url(self) -> str:
        """Get database URL with proper host resolution.

        NOTE: This is used for:
        - Production application (DatabaseService)
        - Integration tests (real PostgreSQL)
        - Alembic migrations

        py-pglite unit tests do NOT use this URL - they create their own.
        """
        # Use explicit DATABASE_URL if provided
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # Auto-resolve host for different environments
        host = self.POSTGRES_HOST

        # If running in Docker container, host should be tux-postgres
        # If running locally, host should be localhost
        if os.getenv("PYTEST_CURRENT_TEST"):
            # Running integration tests - use localhost to access container
            host = "localhost"
        elif os.getenv("TUX_VERSION"):
            # Running in Docker container - use service name
            host = "tux-postgres"

        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_prefix(self) -> str:
        """
        Get command prefix for current environment.

        Returns
        -------
        str
            The configured command prefix.
        """
        return self.BOT_INFO.PREFIX

    def is_prefix_override_enabled(self) -> bool:
        """
        Check if prefix override is enabled by environment variable.

        Returns True if BOT_INFO__PREFIX was explicitly set in environment variables,
        indicating the user wants to override all database prefix settings.

        Returns
        -------
        bool
            True if prefix override is enabled, False otherwise.
        """
        return "BOT_INFO__PREFIX" in os.environ

    def is_debug_enabled(self) -> bool:
        """
        Check if debug mode is enabled.

        Returns
        -------
        bool
            True if debug mode is enabled, False otherwise.
        """
        return self.DEBUG

    def get_cog_ignore_list(self) -> set[str]:
        """
        Get cog ignore list for current environment.

        Returns
        -------
        set[str]
            Set of cog names to ignore.
        """
        return {"test", "example"}

    def get_database_url(self) -> str:
        """
        Legacy method - use database_url property instead.

        Returns
        -------
        str
            The database connection URL.
        """
        return self.database_url

    def get_github_private_key(self) -> str:
        """
        Get the GitHub private key, handling base64 encoding if needed.

        Returns
        -------
        str
            The decoded GitHub private key.
        """
        key = self.EXTERNAL_SERVICES.GITHUB_PRIVATE_KEY
        if key and key.startswith("-----BEGIN"):
            return key
        try:
            return base64.b64decode(key).decode(ENCODING_UTF8) if key else ""
        except Exception:
            return key


# Global configuration instance
CONFIG = Config()  # type: ignore[call-arg]
