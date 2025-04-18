"""Environment management utility for Tux.

This module provides centralized environment configuration management,
following 12-factor app methodology for configuration.
"""

import enum
import os
from pathlib import Path
from typing import Any, Literal, TypeVar

from dotenv import load_dotenv, set_key
from loguru import logger

# Type definitions
EnvType = Literal["dev", "prod"]

T = TypeVar("T")


class EnvError(Exception):
    """Base exception for environment-related errors."""


class ConfigurationError(EnvError):
    """Exception raised for configuration issues."""


class Environment(enum.Enum):
    """Environment types supported by the application."""

    DEVELOPMENT = "dev"
    PRODUCTION = "prod"

    @property
    def is_dev(self) -> bool:
        """Check if this is the development environment."""
        return self == Environment.DEVELOPMENT

    @property
    def is_prod(self) -> bool:
        """Check if this is the production environment."""
        return self == Environment.PRODUCTION


class Config:
    """Configuration manager responsible for handling environment variables."""

    def __init__(self, dotenv_path: Path | None = None, load_env: bool = True):
        """
        Initialize configuration manager.

        Parameters
        ----------
        dotenv_path : Optional[Path]
            Path to .env file
        load_env : bool
            Whether to load environment from .env file
        """
        # Core paths
        self.workspace_root = Path(__file__).parent.parent.parent
        self.dotenv_path = dotenv_path or self.workspace_root / ".env"

        # Load environment variables
        if load_env and self.dotenv_path.exists():
            load_dotenv(dotenv_path=self.dotenv_path, verbose=False)

    def get(self, key: str, default: T | None = None, required: bool = False) -> T | None:
        """
        Get environment variable with type conversion.

        Parameters
        ----------
        key : str
            Environment variable name
        default : Optional[T]
            Default value if not found
        required : bool
            Whether this variable is required

        Returns
        -------
        Optional[T]
            The value of the environment variable

        Raises
        ------
        ConfigurationError
            If variable is required but not found
        """
        value = os.environ.get(key)

        if value is None:
            if required:
                error_msg = f"Required environment variable {key} is not set"
                raise ConfigurationError(error_msg)
            return default

        # If default is provided, attempt to cast to the same type
        if default is not None:
            try:
                if isinstance(default, bool):
                    return value.lower() in ("true", "yes", "1", "y")  # type: ignore
                return type(default)(value)  # type: ignore
            except ValueError as e:
                if required:
                    error_msg = f"Environment variable {key} is not a valid {type(default).__name__}"
                    raise ConfigurationError(error_msg) from e
                return default

        return value  # type: ignore

    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """
        Set environment variable.

        Parameters
        ----------
        key : str
            Environment variable name
        value : Any
            Value to set
        persist : bool
            Whether to persist to .env file
        """
        os.environ[key] = str(value)

        if persist and self.dotenv_path.exists():
            set_key(self.dotenv_path, key, str(value))

    def get_database_url(self, env: Environment) -> str:
        """
        Get database URL for specified environment.

        Parameters
        ----------
        env : Environment
            The environment to get URL for

        Returns
        -------
        str
            Database URL

        Raises
        ------
        ConfigurationError
            If database URL is not configured for environment
        """
        # Get the appropriate database URL key based on the environment
        key = "DEV_DATABASE_URL" if env.is_dev else "PROD_DATABASE_URL"
        url = self.get(key, default="")

        if not url:
            # If no URL is found, raise an error.
            # We no longer provide a default/mock URL here.
            error_msg = f"No database URL found for the {env.value.upper()} environment."
            raise ConfigurationError(error_msg)

        return url

    def get_bot_token(self, env: Environment) -> str:
        """
        Get bot token for specified environment.

        Parameters
        ----------
        env : Environment
            The environment to get token for

        Returns
        -------
        str
            Bot token

        Raises
        ------
        ConfigurationError
            If bot token is not configured for environment
        """
        # Get the appropriate bot token key based on the environment
        key = "DEV_BOT_TOKEN" if env.is_dev else "PROD_BOT_TOKEN"
        token = self.get(key, default="")

        if not token:
            # If no token is found, raise an error.
            error_msg = f"No bot token found for the {env.value.upper()} environment."
            raise ConfigurationError(error_msg)

        return token


class EnvironmentManager:
    """
    Core manager for application environment.

    This class handles all environment-related operations including
    setting the environment mode and managing configuration.
    """

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "EnvironmentManager":
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the environment manager if not already initialized."""
        if getattr(self, "_initialized", False):
            return

        # Core configuration
        self._environment = Environment.DEVELOPMENT  # Default to development
        self._config = Config()
        self._initialized = True

    @property
    def environment(self) -> Environment:
        """Get the current environment."""
        return self._environment

    @environment.setter
    def environment(self, value: Environment) -> None:
        """
        Set the environment.

        Parameters
        ----------
        value : Environment
            The new environment
        """
        if self._environment == value:
            return  # No change

        self._environment = value
        logger.debug(f"Running in {'development' if value.is_dev else 'production'} mode")

    @property
    def config(self) -> Config:
        """Get the configuration manager."""
        return self._config

    def configure(self, environment: Environment) -> None:
        """
        Configure the environment mode.

        Parameters
        ----------
        environment : Environment
            The environment mode to set (DEVELOPMENT or PRODUCTION)
        """
        self.environment = environment


# Create the global instance
_env_manager = EnvironmentManager()


# Public API - simplified interface to the environment manager


def is_dev_mode() -> bool:
    """Check if application is running in development mode."""
    return _env_manager.environment.is_dev


def is_prod_mode() -> bool:
    """Check if application is running in production mode."""
    return _env_manager.environment.is_prod


def get_current_env() -> str:
    """Get current environment name."""
    return _env_manager.environment.value


def set_env_mode(dev_mode: bool) -> None:
    """
    Set environment mode.

    Parameters
    ----------
    dev_mode : bool
        True for development, False for production
    """
    env_mode = Environment.DEVELOPMENT if dev_mode else Environment.PRODUCTION
    _env_manager.configure(env_mode)


def get_database_url() -> str:
    """
    Get database URL for current environment.

    Returns
    -------
    str
        Database URL
    """
    return _env_manager.config.get_database_url(_env_manager.environment)


def get_bot_token() -> str:
    """
    Get bot token for current environment.

    Returns
    -------
    str
        Bot token
    """
    return _env_manager.config.get_bot_token(_env_manager.environment)


def get_config() -> Config:
    """
    Get configuration manager.

    Returns
    -------
    Config
        The config manager
    """
    return _env_manager.config


def configure_environment(dev_mode: bool) -> None:
    """
    Configure the global application environment mode.

    Parameters
    ----------
    dev_mode : bool
        True to set development mode, False to set production mode.
    """
    env_mode = Environment.DEVELOPMENT if dev_mode else Environment.PRODUCTION
    _env_manager.configure(env_mode)
