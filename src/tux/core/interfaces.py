"""Service and bot interfaces using Python protocols for type safety.

This module defines the contracts for services using Python protocols,
enabling structural typing and better testability.
"""

from collections.abc import Mapping
from types import ModuleType
from typing import Any, Protocol, runtime_checkable

import discord

from tux.database.controllers import DatabaseController


class IGithubService(Protocol):
    """Protocol for GitHub service operations.

    Provides access to GitHub API functionality.
    """

    async def get_repo(self) -> Any:
        """Get the repository information.

        Returns:
            The repository data
        """
        ...


class ILoggerService(Protocol):
    """Protocol for logging service operations.

    Provides centralized logging configuration and management.
    """

    def setup_logging(self, level: str = "INFO") -> None:
        """Set up logging configuration.

        Args:
            level: The logging level to use
        """
        ...


class IDatabaseService(Protocol):
    """Protocol for database service operations.

    Provides access to database controllers and query execution capabilities.
    """

    def get_controller(self) -> DatabaseController:
        """Get the database controller instance.

        Returns:
            The database controller for performing database operations
        """
        ...

    async def execute_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a database query operation.

        Args:
            operation: The operation name to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the database operation
        """
        ...

    async def connect(self) -> None:
        """Establish the database connection."""
        ...

    def is_connected(self) -> bool:
        """Check if the database client is connected."""
        ...

    def is_registered(self) -> bool:
        """Check if the database models are registered/ready."""
        ...

    async def disconnect(self) -> None:
        """Close the database connection if connected."""
        ...


class IBotService(Protocol):
    """Protocol for bot service operations.

    Provides access to bot properties and operations like user/emoji access.
    """

    @property
    def latency(self) -> float:
        """Get the bot's current latency to Discord.

        Returns:
            The latency in seconds
        """
        ...

    def get_user(self, user_id: int) -> discord.User | None:
        """Get a user by their ID.

        Args:
            user_id: The Discord user ID

        Returns:
            The user object if found, None otherwise
        """
        ...

    def get_emoji(self, emoji_id: int) -> discord.Emoji | None:
        """Get an emoji by its ID.

        Args:
            emoji_id: The Discord emoji ID

        Returns:
            The emoji object if found, None otherwise
        """
        ...

    @property
    def user(self) -> discord.ClientUser | None:
        """Get the bot's user object.

        Returns:
            The bot's user object if available
        """
        ...

    @property
    def guilds(self) -> list[discord.Guild]:
        """Get all guilds the bot is in.

        Returns:
            List of guild objects
        """
        ...


class IConfigService(Protocol):
    """Protocol for configuration service operations.

    Provides access to configuration values and settings.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key to retrieve
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """
        ...

    def get_database_url(self) -> str:
        """Get the database URL for the current environment.

        Returns:
            The database connection URL
        """
        ...

    def get_bot_token(self) -> str:
        """Get the bot token for the current environment.

        Returns:
            The Discord bot token
        """
        ...

    def is_dev_mode(self) -> bool:
        """Check if the bot is running in development mode.

        Returns:
            True if in development mode, False otherwise
        """
        ...


@runtime_checkable
class IReloadableBot(Protocol):
    """Protocol for bot-like objects that support extension management.

    This enables hot-reload and cog management utilities to operate on any
    bot-like object that exposes the expected interface without importing
    the concrete bot implementation.
    """

    @property
    def extensions(self) -> Mapping[str, ModuleType]: ...

    help_command: Any

    async def load_extension(self, name: str) -> None: ...

    async def reload_extension(self, name: str) -> None: ...

    async def add_cog(self, cog: Any, /, *, override: bool = False) -> None: ...

    # Optional attribute; kept as Any to avoid import-time cycles
    sentry_manager: Any
