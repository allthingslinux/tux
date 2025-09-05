"""Main Tux configuration using Pydantic Settings.

This module provides the main configuration class and global instance,
using the extracted models and proper pydantic-settings for environment variable binding.
"""

import base64
import os
import warnings

from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

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


def load_environment() -> None:
    """Load environment variables from .env file once at application startup.

    This is called automatically when the config module is imported.
    Priority: Existing env vars > .env file > defaults
    """
    load_dotenv(dotenv_path=".env", override=False)


def validate_environment() -> None:
    """Validate critical environment variables for security and correctness."""
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
    if db_password and len(db_password) < 12 and db_password not in ["ChangeThisToAStrongPassword123!"]:
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


# Load environment when module is imported
load_environment()
validate_environment()


class Config(BaseSettings):
    """Main Tux configuration using Pydantic Settings."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Core configuration
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Bot tokens
    BOT_TOKEN: str = Field(default="", description="Discord bot token")

    # Database configuration (standard PostgreSQL env vars)
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="tuxdb", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="tuxuser", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="ChangeThisToAStrongPassword123!", description="PostgreSQL password")

    # Optional: Custom database URL override
    DATABASE_URL: str = Field(default="", description="Custom database URL override")

    # Bot info
    BOT_INFO: BotInfo = Field(default_factory=BotInfo)

    # User permissions
    USER_IDS: UserIds = Field(default_factory=UserIds)
    ALLOW_SYSADMINS_EVAL: bool = Field(default=False, description="Allow sysadmins to use eval")

    # Features
    STATUS_ROLES: StatusRoles = Field(default_factory=StatusRoles)
    TEMPVC: TempVC = Field(default_factory=TempVC)
    GIF_LIMITER: GifLimiter = Field(default_factory=GifLimiter)
    XP_CONFIG: XP = Field(default_factory=XP)
    SNIPPETS: Snippets = Field(default_factory=Snippets)
    IRC_CONFIG: IRC = Field(default_factory=IRC)

    # External services
    EXTERNAL_SERVICES: ExternalServices = Field(default_factory=ExternalServices)

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
        """Get command prefix for current environment."""
        return self.BOT_INFO.PREFIX

    def is_prefix_override_enabled(self) -> bool:
        """Check if prefix override is enabled by environment variable.

        Returns True if BOT_INFO__PREFIX was explicitly set in environment variables,
        indicating the user wants to override all database prefix settings.
        """

        return "BOT_INFO__PREFIX" in os.environ

    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.DEBUG

    def get_cog_ignore_list(self) -> set[str]:
        """Get cog ignore list for current environment."""
        return {"test", "example"}

    def get_database_url(self) -> str:
        """Legacy method - use database_url property instead."""
        return self.database_url

    def get_github_private_key(self) -> str:
        """Get the GitHub private key, handling base64 encoding if needed."""
        key = self.EXTERNAL_SERVICES.GITHUB_PRIVATE_KEY
        if key and key.startswith("-----BEGIN"):
            return key
        try:
            return base64.b64decode(key).decode("utf-8") if key else ""
        except Exception:
            return key


# Global configuration instance
CONFIG = Config()
