"""Enhanced base cog with database access and usage generation.

This module provides the `BaseCog` class that:
- Provides access to database services
- Generates command usage strings from function signatures
"""

from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any

from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseCoordinator
from tux.shared.config import CONFIG
from tux.shared.functions import generate_usage as _generate_usage_shared

if TYPE_CHECKING:
    from tux.core.bot import Tux


class BaseCog(commands.Cog):
    """Enhanced base cog class with database access.

    This class provides access to database services and configuration.
    """

    _unload_task: asyncio.Task[None] | None = None

    def __init__(self, bot: Tux) -> None:
        """Initialize the base cog.

        Args:
            bot: The Tux bot instance
        """
        super().__init__()
        # Get the bot instance
        self.bot = bot

        # Configure automatic usage strings for commands that do not set one
        self._setup_command_usage()

    # ---------- Usage generation ----------
    def _setup_command_usage(self) -> None:
        """Generate usage strings for all commands on this cog when missing.

        The generated usage follows the pattern:
        "<qualified_name> <param tokens>"
        where each required parameter is denoted as "<name: Type>" and optional
        parameters are denoted as "[name: Type]". The prefix is intentionally
        omitted because it's context-dependent and provided by `ctx.prefix`.
        """
        try:
            for command in self.get_commands():
                # Respect explicit usage if provided by the command
                if getattr(command, "usage", None):
                    continue
                command.usage = self._generate_usage(command)
        except Exception as e:
            logger.debug(f"Failed to setup command usage for {self.__class__.__name__}: {e}")

    def _generate_usage(self, command: commands.Command[Any, ..., Any]) -> str:
        """Generate a usage string with flag support when available.

        Detects a `flags` parameter annotated with a `commands.FlagConverter` subclass
        and delegates to the shared usage generator for consistent formatting.
        Fallbacks to simple positional/optional parameter rendering otherwise.
        """
        flag_converter: type[commands.FlagConverter] | None = None
        try:
            signature = inspect.signature(command.callback)
            for name, param in signature.parameters.items():
                if name != "flags":
                    continue
                ann = param.annotation
                if (
                    ann is not inspect.Signature.empty
                    and isinstance(ann, type)
                    and issubclass(
                        ann,
                        commands.FlagConverter,
                    )
                ):
                    flag_converter = ann
                    break
        except Exception:
            # If inspection fails, defer to simple name
            return command.qualified_name

        # Use the shared generator to keep behavior consistent across cogs
        try:
            return _generate_usage_shared(command, flag_converter)
        except Exception:
            # Final fallback: minimal usage string
            return command.qualified_name

    @property
    def db(self) -> DatabaseCoordinator:
        """Get the database coordinator for accessing database controllers.

        Returns:
            The database coordinator instance
        """
        return self.bot.db

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value directly from CONFIG.

        Args:
            key: The configuration key to retrieve
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """

        try:
            # Handle nested keys like "BOT_INFO.BOT_NAME"
            keys = key.split(".")
            value = CONFIG

            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
        except Exception as e:
            logger.error(f"Failed to get config value {key}: {e}")
            return default
        else:
            return value

    def get_bot_latency(self) -> float:
        """Get the bot's latency.

        Returns:
            The bot's latency in seconds
        """
        return self.bot.latency

    def get_bot_user(self, user_id: int) -> Any:
        """Get a user by ID.

        Args:
            user_id: The Discord user ID

        Returns:
            The user object if found, None otherwise
        """
        return self.bot.get_user(user_id)

    def get_bot_emoji(self, emoji_id: int) -> Any:
        """Get an emoji by ID.

        Args:
            emoji_id: The Discord emoji ID

        Returns:
            The emoji object if found, None otherwise
        """
        return self.bot.get_emoji(emoji_id)

    def __repr__(self) -> str:
        """Return a string representation of the cog."""
        bot_user = getattr(self.bot, "user", "Unknown")
        return f"<{self.__class__.__name__} bot={bot_user}>"

    def unload_if_missing_config(self, condition: bool, config_name: str, extension_name: str) -> bool:
        """Gracefully unload this cog if configuration is missing.

        Args:
            condition: True if config is missing (will trigger unload)
            config_name: Name of the missing configuration for logging
            extension_name: Full extension name for unloading

        Returns:
            True if unload was triggered, False otherwise
        """
        if condition:
            logger.warning(f"{config_name} is not configured. {self.__class__.__name__} will be unloaded.")
            self._unload_task = asyncio.create_task(self._unload_self(extension_name))
            return True
        return False

    async def _unload_self(self, extension_name: str) -> None:
        """Unload this cog if configuration is missing."""
        try:
            await self.bot.unload_extension(extension_name)
            logger.info(f"{self.__class__.__name__} has been unloaded due to missing configuration")
        except Exception as e:
            logger.error(f"Failed to unload {self.__class__.__name__}: {e}")
