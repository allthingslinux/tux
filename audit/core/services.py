"""Service implementations for dependency injection."""

from __future__ import annotations

from typing import Any

import discord
from loguru import logger

from tux.core.interfaces import (
    IConfigurationService,
    IDatabaseService,
    IEmbedService,
    IExternalAPIService,
    ILoggingService,
)
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils.config import Config
from tux.wrappers.github import GithubService


class DatabaseService(IDatabaseService):
    """Database service implementation."""

    def __init__(self) -> None:
        self._controller = DatabaseController()

    def get_controller(self) -> DatabaseController:
        """Get the database controller instance."""
        return self._controller


class ConfigurationService(IConfigurationService):
    """Configuration service implementation."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(Config, key, default)

    def get_required(self, key: str) -> Any:
        """Get a required configuration value."""
        if not hasattr(Config, key):
            msg = f"Required configuration key '{key}' not found"
            raise ValueError(msg)
        return getattr(Config, key)


class EmbedService(IEmbedService):
    """Embed creation service implementation."""

    def __init__(self, bot: Any) -> None:
        self.bot = bot

    def create_info_embed(self, title: str, description: str, **kwargs: Any) -> discord.Embed:
        """Create an info embed."""
        return EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            title=title,
            description=description,
            **kwargs,
        )

    def create_error_embed(self, title: str, description: str, **kwargs: Any) -> discord.Embed:
        """Create an error embed."""
        return EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.ERROR,
            title=title,
            description=description,
            **kwargs,
        )

    def create_success_embed(self, title: str, description: str, **kwargs: Any) -> discord.Embed:
        """Create a success embed."""
        return EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.SUCCESS,
            title=title,
            description=description,
            **kwargs,
        )


class GitHubAPIService(IExternalAPIService):
    """GitHub API service implementation."""

    def __init__(self) -> None:
        self._github_service = GithubService()

    async def is_available(self) -> bool:
        """Check if the GitHub service is available."""
        try:
            await self._github_service.get_repo()
            return True
        except Exception as e:
            logger.warning(f"GitHub service unavailable: {e}")
            return False

    def get_service(self) -> GithubService:
        """Get the underlying GitHub service."""
        return self._github_service


class LoggingService(ILoggingService):
    """Logging service implementation."""

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        logger.info(message, **kwargs)

    def log_error(self, message: str, error: Exception | None = None, **kwargs: Any) -> None:
        """Log an error message."""
        if error:
            logger.error(f"{message}: {error}", **kwargs)
        else:
            logger.error(message, **kwargs)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        logger.warning(message, **kwargs)
