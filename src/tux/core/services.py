"""Concrete service implementations for dependency injection.

This module provides concrete implementations of the service interfaces,
wrapping existing functionality while maintaining backward compatibility.
"""

import asyncio
from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.services.database.client import db
from tux.services.database.controllers import DatabaseController
from tux.services.logger import setup_logging as setup_rich_logging
from tux.services.wrappers.github import GithubService as GitHubWrapper
from tux.shared.config.env import is_dev_mode
from tux.shared.config.settings import Config


class GitHubService:
    """Concrete implementation of IGithubService.

    Wraps the GitHub API wrapper to provide a clean service interface.
    """

    def __init__(self) -> None:
        """Initialize the GitHub service."""
        self._github_wrapper: GitHubWrapper | None = None
        logger.debug("GitHubService initialized")

    def get_wrapper(self) -> GitHubWrapper:
        """Get the GitHub wrapper instance.

        Returns:
            The GitHub wrapper for performing GitHub operations
        """
        if self._github_wrapper is None:
            self._github_wrapper = GitHubWrapper()
            logger.debug("GitHubWrapper instantiated")

        return self._github_wrapper

    async def get_repo(self) -> Any:
        """Get the repository information.

        Returns:
            The repository data
        """
        try:
            wrapper = self.get_wrapper()
            return await wrapper.get_repo()
        except Exception as e:
            logger.error(f"Failed to get repository: {e}")
            raise


class LoggerService:
    """Concrete implementation of ILoggerService.

    Provides centralized logging configuration and management.
    """

    def __init__(self) -> None:
        """Initialize the logger service."""
        logger.debug("LoggerService initialized")

    def setup_logging(self, level: str = "INFO") -> None:
        """Set up logging configuration.

        Args:
            level: The logging level to use
        """
        try:
            # The rich logging setup currently doesn't take a level parameter; it configures handlers.
            setup_rich_logging()
            logger.debug(f"Logging configured with level: {level}")
        except Exception as e:
            logger.error(f"Failed to setup logging: {e}")
            raise


class DatabaseService:
    """Concrete implementation of IDatabaseService.

    Wraps the existing DatabaseController to provide a clean service interface
    while maintaining backward compatibility with existing functionality.
    """

    def __init__(self) -> None:
        """Initialize the database service."""
        self._controller: DatabaseController | None = None
        logger.debug("DatabaseService initialized")

    def get_controller(self) -> DatabaseController:
        """Get the database controller instance.

        Returns:
            The database controller for performing database operations
        """
        if self._controller is None:
            self._controller = DatabaseController()
            logger.debug("DatabaseController instantiated")

        return self._controller

    async def execute_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a database query operation.

        Args:
            operation: The operation name to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the database operation

        Raises:
            AttributeError: If the operation doesn't exist on the controller
            Exception: If the database operation fails
        """

        def _raise_operation_error() -> None:
            """Raise an error for missing operation."""
            error_msg = f"DatabaseController has no operation '{operation}'"
            raise AttributeError(error_msg)

        try:
            controller = self.get_controller()

            if not hasattr(controller, operation):
                _raise_operation_error()

            method = getattr(controller, operation)

            if not callable(method):
                logger.warning(f"Operation '{operation}' is not callable")
                value = method
            else:
                if asyncio.iscoroutinefunction(method):
                    value = await method(*args, **kwargs)
                else:
                    value = method(*args, **kwargs)
                logger.debug(f"Executed database operation: {operation}")
        except Exception as e:
            logger.error(f"Database operation '{operation}' failed: {e}")
            raise
        else:
            return value

    async def connect(self) -> None:
        """Establish the database connection using the shared client."""
        await db.connect()

    def is_connected(self) -> bool:
        """Return whether the database client is connected."""
        return db.is_connected()

    def is_registered(self) -> bool:
        """Return whether models are registered (auto-register follows connection)."""
        return db.is_registered()

    async def disconnect(self) -> None:
        """Disconnect the database client if connected."""
        if db.is_connected():
            await db.disconnect()

    def _validate_operation(self, controller: DatabaseController, operation: str) -> None:
        """Validate that an operation exists on the controller.

        Args:
            controller: The database controller
            operation: The operation name to validate

        Raises:
            AttributeError: If the operation doesn't exist
        """
        if not hasattr(controller, operation):
            error_msg = f"DatabaseController has no operation '{operation}'"
            raise AttributeError(error_msg)


class BotService:
    """Concrete implementation of IBotService.

    Provides access to bot properties and operations while wrapping
    the discord.py Bot instance.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the bot service.

        Args:
            bot: The Discord bot instance
        """
        self._bot = bot
        # Expose bot as a public property for container validation
        self.bot = bot
        logger.debug("BotService initialized")

    @property
    def latency(self) -> float:
        """Get the bot's current latency to Discord.

        Returns:
            The latency in seconds
        """
        return self._bot.latency

    def get_user(self, user_id: int) -> discord.User | None:
        """Get a user by their ID.

        Args:
            user_id: The Discord user ID

        Returns:
            The user object if found, None otherwise
        """
        try:
            return self._bot.get_user(user_id)
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    def get_emoji(self, emoji_id: int) -> discord.Emoji | None:
        """Get an emoji by its ID.

        Args:
            emoji_id: The Discord emoji ID

        Returns:
            The emoji object if found, None otherwise
        """
        try:
            return self._bot.get_emoji(emoji_id)
        except Exception as e:
            logger.error(f"Failed to get emoji {emoji_id}: {e}")
            return None

    @property
    def user(self) -> discord.ClientUser | None:
        """Get the bot's user object.

        Returns:
            The bot's user object if available
        """
        return self._bot.user

    @property
    def guilds(self) -> list[discord.Guild]:
        """Get all guilds the bot is in.

        Returns:
            List of guild objects
        """
        return list(self._bot.guilds)


class ConfigService:
    """Concrete implementation of IConfigService.

    Provides access to configuration values and settings while wrapping
    the existing Config utility.
    """

    def __init__(self) -> None:
        """Initialize the config service."""
        self._config = Config()
        logger.debug("ConfigService initialized")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key to retrieve
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """
        try:
            # Try to get the attribute from Config class
            if hasattr(self._config, key):
                value = getattr(self._config, key)
            else:
                logger.warning(
                    f"Configuration key '{key}' not found, returning default: {default}",
                )
                value = default
        except Exception as e:
            logger.error(f"Failed to get config key '{key}': {e}")
            return default
        else:
            return value

    def get_database_url(self) -> str:
        """Get the database URL for the current environment.

        Returns:
            The database connection URL
        """
        try:
            return self._config.DATABASE_URL
        except Exception as e:
            logger.error(f"Failed to get database URL: {e}")
            raise

    def get_bot_token(self) -> str:
        """Get the bot token for the current environment.

        Returns:
            The Discord bot token
        """
        try:
            return self._config.BOT_TOKEN
        except Exception as e:
            logger.error(f"Failed to get bot token: {e}")
            raise

    def is_dev_mode(self) -> bool:
        """Check if the bot is running in development mode.

        Returns:
            True if in development mode, False otherwise
        """
        try:
            return is_dev_mode()
        except Exception as e:
            logger.error(f"Failed to check dev mode: {e}")
            return False
