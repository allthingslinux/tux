"""Environment management utility for Tux.

This module provides centralized environment configuration management,
following 12-factor app methodology for configuration.
"""

import enum
import os
import sys
from dataclasses import dataclass, field
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


@dataclass
class CommandContext:
    """Context information about the current command."""

    command: str | None = None
    args: list[str] = field(default_factory=list)

    @property
    def is_help_command(self) -> bool:
        """Check if the current command is a help command."""
        if not self.command:
            return False
        # Check command itself and also the first argument for help flags
        if self.command in ("-h", "--help", "help"):
            return True
        return len(self.args) > 0 and self.args[0] in ("-h", "--help")

    @property
    def is_db_command(self) -> bool:
        """Check if the current command is the database group command."""
        return self.command == "db" if self.command else False

    def needs_database(self) -> bool:
        """Determine if the current command needs database access."""
        if not self.command:
            return False

        # Help commands never need a database
        if self.is_help_command:
            return False

        no_db_required_commands_or_groups = {
            "lint",
            "lint-fix",
            "format",
            "typecheck",
            "check",  # dev commands
            "dev",  # dev group itself
            "docs",  # docs group itself
            "serve",
            "build",  # docs commands
        }

        # Check both parts if colon is present (group:command format)
        if ":" in self.command:
            group_part, command_part = self.command.split(":", 1)
            # Check if the group OR the specific command doesn't need DB
            if group_part in no_db_required_commands_or_groups or command_part in no_db_required_commands_or_groups:
                return False
        # Check the command directly if no colon
        elif self.command in no_db_required_commands_or_groups:
            return False

        # If none of the above, it needs a database
        return True

    @classmethod
    def from_argv(cls) -> "CommandContext":
        """Create a CommandContext from sys.argv."""
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        return cls(command=args[0] if args else None, args=args[1:])


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
        # For development commands that don't need a real database
        cmd_ctx = CommandContext.from_argv()

        # If this is a CLI help command or a command that doesn't need DB
        if cmd_ctx.is_help_command or not cmd_ctx.needs_database():
            return "postgresql://postgres:postgres@postgres:1234/postgres"  # Return dummy URL

        # Check for any --help flag in arguments
        if "--help" in sys.argv or "-h" in sys.argv:
            return "postgresql://postgres:postgres@postgres:1234/postgres"  # Return dummy URL

        # Get the appropriate database URL
        key = "DEV_DATABASE_URL" if env.is_dev else "PROD_DATABASE_URL"
        url = self.get(key, default="")

        if not url:
            # Allow CLI to run with a mock URL for development
            if "python" in sys.argv[0] and "-m" in sys.argv and "tux" in sys.argv:
                logger.warning(f"No database URL configured for {env.value.upper()} environment. Using mock URL.")
                return "postgresql://postgres:postgres@postgres:1234/postgres"

            error_msg = (
                f"No database URL configured for {env.value.upper()} environment. Please set {key} in your environment."
            )
            raise ConfigurationError(error_msg)

        return url


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
        self._environment = Environment.DEVELOPMENT
        self._config = Config()
        self._setup_complete = False
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
        self._setup_complete = False  # Reset setup flag on environment change

        # Log the change
        logger.debug(f"Running in {'development' if value.is_dev else 'production'} mode")

    @property
    def config(self) -> Config:
        """Get the configuration manager."""
        return self._config

    def determine_environment(self, args: list[str] | None = None) -> Environment:
        """
        Determine environment from command line arguments.
        Defaults to DEVELOPMENT unless --prod is explicitly passed.

        Parameters
        ----------
        args : Optional[list[str]]
            Command line arguments

        Returns
        -------
        Environment
            The determined environment
        """
        if args is None:
            args = sys.argv[1:] if len(sys.argv) > 1 else []

        # Check explicit --prod flag first
        if "--prod" in args:
            return Environment.PRODUCTION

        # Otherwise, default to Development
        # This includes cases where --dev is passed or no flags are passed.
        return Environment.DEVELOPMENT

    def setup_database_url(self) -> None:
        """
        Configure DATABASE_URL environment variable.

        Sets up the proper database URL based on current environment.
        """
        # Skip if already set up or not needed
        if self._setup_complete:
            return

        cmd_ctx = CommandContext.from_argv()
        if not cmd_ctx.needs_database():
            self._setup_complete = True
            return

        # Get URL and set environment variable
        url = self.config.get_database_url(self.environment)
        self.config.set("DATABASE_URL", url, persist=True)

        self._setup_complete = True

        # Log database setup
        logger.debug(f"Database URL set for {self.environment.value} environment: {url}")

    def configure(self, args: list[str] | None = None) -> None:
        """
        Configure the environment based on command line arguments.

        Parameters
        ----------
        args : Optional[list[str]]
            Command line arguments
        """
        self.environment = self.determine_environment(args)
        self.setup_database_url()


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
    _env_manager.environment = Environment.DEVELOPMENT if dev_mode else Environment.PRODUCTION


def get_database_url() -> str:
    """
    Get database URL for current environment.

    Returns
    -------
    str
        Database URL
    """
    return _env_manager.config.get_database_url(_env_manager.environment)


def setup_database_url() -> None:
    """Configure DATABASE_URL environment variable."""
    _env_manager.setup_database_url()


def get_config() -> Config:
    """
    Get configuration manager.

    Returns
    -------
    Config
        The config manager
    """
    return _env_manager.config


def parse_env_flags(args: list[str] | None = None) -> bool:
    """
    Parse environment flags.

    Parameters
    ----------
    args : Optional[list[str]]
        Command line arguments

    Returns
    -------
    bool
        True for development, False for production
    """
    return _env_manager.determine_environment(args).is_dev


def configure_env_from_args(args: list[str] | None = None) -> None:
    """
    Configure environment from arguments.

    Parameters
    ----------
    args : Optional[list[str]]
        Command line arguments
    """
    _env_manager.configure(args)
