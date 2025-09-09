"""Service and bot interfaces using Python protocols for type safety.

This module defines the contracts for services using Python protocols,
enabling structural typing and better testability.
"""

from collections.abc import Mapping
from types import ModuleType
from typing import Any, Protocol, runtime_checkable

import discord


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
