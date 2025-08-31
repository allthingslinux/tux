"""Concrete service implementations for dependency injection.

This module provides concrete implementations of the service interfaces,
wrapping existing functionality while maintaining backward compatibility.
"""

from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.services.logger import setup_logging as setup_rich_logging
from tux.services.wrappers.github import GithubService as GitHubWrapper


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
            logger.error(f"❌ Failed to get repository: {type(e).__name__}")
            logger.info("💡 Check your GitHub API configuration and network connection")
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
            logger.error(f"❌ Failed to setup logging: {type(e).__name__}")
            logger.info("💡 Check your logging configuration and dependencies")
            raise


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
