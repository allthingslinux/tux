"""
Enhanced base cog with database access and automatic usage generation.

This module provides the BaseCog class, which serves as the foundation for all
bot cogs. It provides convenient access to database services, configuration
values, and automatically generates command usage strings from function signatures
and type hints.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any

from discord.ext import commands
from loguru import logger

from tux.shared.config import CONFIG
from tux.shared.functions import generate_usage

if TYPE_CHECKING:
    from tux.core.bot import Tux
    from tux.database.controllers import DatabaseCoordinator

__all__ = ["BaseCog"]


class BaseCog(commands.Cog):
    """
    Enhanced base cog class providing database access and automatic usage generation.

    Foundation for all bot cogs, offering convenient access to database controllers,
    configuration values, and automatic command usage string generation.

    Attributes
    ----------
    bot : Tux
        The bot instance this cog is attached to.
    _unload_task : asyncio.Task[None] | None
        Background task for graceful cog unloading when config is missing.
    """

    _unload_task: asyncio.Task[None] | None = None

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the base cog with bot instance and command usage setup.

        Automatically generates usage strings for all commands in this cog
        that don't have explicit usage strings defined.

        Parameters
        ----------
        bot : Tux
            The bot instance this cog will be attached to.
        """
        super().__init__()

        # Store bot instance for access to services and state
        self.bot = bot

        # Automatically generate usage strings for commands without explicit usage
        self._setup_command_usage()

    def _setup_command_usage(self) -> None:
        """
        Generate usage strings for all commands in this cog that lack explicit usage.

        Generated usage follows: ``<qualified_name> <param tokens>`` where required
        parameters are ``<name: Type>`` and optional are ``[name: Type]``. Prefix
        is omitted (provided by ``ctx.prefix``). Respects explicit usage strings
        if already set. Errors are logged but don't prevent cog loading.

        Examples
        --------
        ``ban <member: Member> [reason: str]``
        ``config set <key: str> <value: str>``
        """
        try:
            for command in self.get_commands():
                # Skip commands that already have explicit usage defined
                if getattr(command, "usage", None):
                    continue

                # Generate usage from command signature and type hints
                command.usage = self._generate_usage(command)

        except Exception:
            # Log but don't crash - cog can still load without usage strings
            logger.exception(
                f"Failed to setup command usage for {self.__class__.__name__}",
            )

    def _generate_usage(self, command: commands.Command[Any, ..., Any]) -> str:
        """
        Generate a usage string with support for flags and positional parameters.

        Inspects the command's callback signature to detect FlagConverter parameters
        and positional parameters. Delegates to shared usage generator for consistency.
        Falls back to command name if generation fails.

        Parameters
        ----------
        command : commands.Command
            The command to generate usage for.

        Returns
        -------
        str
            Generated usage string, or qualified command name as fallback.
        """
        flag_converter: type[commands.FlagConverter] | None = None

        try:
            # Inspect the command callback's signature to detect flag parameters
            signature = inspect.signature(command.callback)

            for name, param in signature.parameters.items():
                # Look specifically for a parameter named "flags"
                if name != "flags":
                    continue

                # Check if it's annotated with a FlagConverter subclass
                ann = param.annotation
                if (
                    ann is not inspect.Signature.empty
                    and isinstance(ann, type)
                    and issubclass(ann, commands.FlagConverter)
                ):
                    flag_converter = ann
                    break

        except Exception:
            # If signature inspection fails, fall back to minimal usage
            logger.trace(
                f"Signature inspection failed for {command.qualified_name}, using fallback",
            )
            return command.qualified_name

        # Delegate to shared usage generator for consistent formatting
        try:
            return generate_usage(command, flag_converter)
        except Exception:
            # Final fallback: just return the command name
            logger.trace(
                f"Usage generation failed for {command.qualified_name}, using fallback",
            )
            return command.qualified_name

    @property
    def db(self) -> DatabaseCoordinator:
        """
        Get the database coordinator for accessing database controllers.

        Provides convenient access to database operations without needing to
        access ``self.bot.db`` directly.

        Returns
        -------
        DatabaseCoordinator
            Coordinator providing access to all database controllers.

        Examples
        --------
        >>> await self.db.guild_config.get_guild_config(guild_id)
        >>> await self.db.cases.create_case(...)
        """
        return self.bot.db

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from CONFIG with support for nested keys.

        Supports dot notation for nested values (e.g., ``"BOT_INFO.BOT_NAME"``).
        Errors during retrieval are logged but don't raise exceptions.

        Parameters
        ----------
        key : str
            The configuration key to retrieve.
        default : Any, optional
            Default value to return if key is not found. Defaults to None.

        Returns
        -------
        Any
            The configuration value or default if not found.

        Examples
        --------
        >>> self.get_config("BOT_INFO.BOT_NAME")
        'Tux'
        >>> self.get_config("MISSING_KEY", "fallback")
        'fallback'
        """
        try:
            # Support nested keys like "BOT_INFO.BOT_NAME"
            keys = key.split(".")
            value = CONFIG

            # Navigate through nested attributes
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default

        except Exception:
            # Log error but return default gracefully
            logger.exception(f"Failed to get config value {key}")
            return default
        else:
            return value

    def __repr__(self) -> str:
        """
        Return a string representation of the cog instance.

        Returns
        -------
        str
            String representation in format ``<CogName bot=BotUser>``.
        """
        bot_user = getattr(self.bot, "user", "Unknown")
        return f"<{self.__class__.__name__} bot={bot_user}>"

    def unload_if_missing_config(self, *, condition: bool, config_name: str) -> bool:
        """
        Check if required configuration is missing and log warning.

        Allows cogs to detect missing configuration at load time and return
        early from __init__ to prevent partial initialization. When this returns
        True, the cog's __init__ should return early. The cog will be loaded but
        commands won't be registered properly, preventing runtime errors.

        Parameters
        ----------
        condition : bool
            True if config is missing (should unload), False otherwise.
        config_name : str
            Name of the missing configuration for logging purposes.

        Returns
        -------
        bool
            True if config is missing (caller should return early), False if config is present.

        Examples
        --------
        >>> def __init__(self, bot: Tux):
        ...     super().__init__(bot)
        ...     if self.unload_if_missing_config(
        ...         condition=not CONFIG.GITHUB_TOKEN,
        ...         config_name="GITHUB_TOKEN",
        ...     ):
        ...         return  # Exit early, cog will be partially loaded
        ...     self.github_client = GitHubClient()
        """
        if condition:
            # Get the module name from the stack
            cog_module = next(
                (
                    f.frame.f_locals["self"].__class__.__module__
                    for f in inspect.stack()
                    if "self" in f.frame.f_locals
                    and isinstance(f.frame.f_locals["self"], commands.Cog)
                ),
                "UnknownModule",
            )
            logger.warning(
                f"{config_name} is not configured. {cog_module} will be unloaded.",
            )

            # Schedule async unload in background to avoid blocking initialization
            self._unload_task = asyncio.create_task(self._unload_self(cog_module))

        return condition

    async def _unload_self(self, extension_name: str) -> None:
        """
        Perform the actual cog unload operation.

        Called as a background task by ``unload_if_missing_config()``.
        Errors during unload are logged but don't raise exceptions.

        Parameters
        ----------
        extension_name : str
            Full extension name to unload.
        """
        try:
            await self.bot.unload_extension(extension_name)
            logger.info(
                f"{self.__class__.__name__} unloaded due to missing configuration",
            )
        except Exception:
            logger.exception(f"Failed to unload {self.__class__.__name__}")
