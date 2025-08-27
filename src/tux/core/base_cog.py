"""Enhanced base cog with automatic dependency injection and usage generation.

This module provides the `BaseCog` class that:
- Injects services via the dependency injection container
- Generates command usage strings from function signatures

Backwards-compatibility fallbacks have been removed; cogs are expected to run
with a configured service container.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from discord.ext import commands
from loguru import logger

from tux.core.interfaces import IBotService, IConfigService, ILoggerService
from tux.database.service import DatabaseService
from tux.shared.functions import generate_usage as _generate_usage_shared

if TYPE_CHECKING:
    from tux.core.types import Tux


class BaseCog(commands.Cog):
    """Enhanced base cog class with automatic dependency injection support.

    This class injects services through the dependency injection container.
    No legacy fallbacks are provided; the container should be available on the
    bot instance and services should be registered as needed by each cog.

    Injected properties:
    - db_service: Database service for database operations
    - bot_service: Bot service for bot-related operations
    - config_service: Configuration service for accessing settings
    - logger_service: Logger service for logging
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the base cog with automatic service injection.

        Args:
            bot: The Tux bot instance

        The constructor injects services through the dependency injection
        container. The container is required; no fallbacks are provided.
        """
        super().__init__()
        # Initialize service properties first
        self.db_service: DatabaseService | None = None
        self.bot_service: IBotService | None = None
        self.config_service: IConfigService | None = None
        self.logger_service: ILoggerService | None = None
        self._db_controller = None  # legacy attribute removed; kept for type stability only

        # Get the bot instance
        self.bot = bot

        # Require a container on the bot
        if not hasattr(bot, "container") or bot.container is None:
            error_msg = f"Service container not available for {self.__class__.__name__}. DI is required."
            raise RuntimeError(error_msg)

        self._container = bot.container
        # Attempt injection
        self._inject_services()

        # Configure automatic usage strings for commands that do not set one
        self._setup_command_usage()

    def _inject_services(self) -> None:
        """Inject services through the dependency injection container.

        Attempts to resolve and inject all available services. If any service
        injection fails, it will be logged; no legacy fallbacks are provided.
        """
        # Inject services in order of dependency
        self._inject_database_service()
        self._inject_bot_service()
        self._inject_config_service()
        self._inject_logger_service()

        # Single summary log for this cog's injection results
        logger.debug(
            f"[BaseCog] Injected services for {self.__class__.__name__} "
            f"(db={self.db_service is not None}, "
            f"bot={self.bot_service is not None}, "
            f"config={self.config_service is not None}, "
            f"logger={self.logger_service is not None})",
        )

    def _inject_database_service(self) -> None:
        """Inject the database service."""
        try:
            self.db_service = self._container.get_optional(DatabaseService)
            if self.db_service:
                logger.trace(f"Injected database service into {self.__class__.__name__}")
            else:
                logger.warning(f"Database service not available for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Database service injection failed for {self.__class__.__name__}: {e}")

    def _inject_bot_service(self) -> None:
        """Inject the bot service."""
        try:
            self.bot_service = self._container.get_optional(IBotService)
            if self.bot_service:
                logger.trace(f"[BaseCog] Injected bot service into {self.__class__.__name__}")
            else:
                logger.warning(f"[BaseCog] Bot service not available for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"[BaseCog] Bot service injection failed for {self.__class__.__name__}: {e}", exc_info=True)

    def _inject_config_service(self) -> None:
        """Inject the config service."""
        try:
            self.config_service = self._container.get_optional(IConfigService)
            if self.config_service:
                logger.trace(f"Injected config service into {self.__class__.__name__}")
            else:
                logger.warning(f"Config service not available for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Config service injection failed for {self.__class__.__name__}: {e}")

    def _inject_logger_service(self) -> None:
        """Inject the logger service (optional)."""
        try:
            self.logger_service = self._container.get_optional(ILoggerService)
            if self.logger_service:
                logger.trace(f"Injected logger service into {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Logger service injection failed for {self.__class__.__name__}: {e}")

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
            signature = inspect.signature(command.callback)  # type: ignore[attr-defined]
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
                    flag_converter = ann  # type: ignore[assignment]
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

    # (Embed helpers and error handling intentionally omitted as requested.)

    @property
    def db(self):
        """Get the database controller from the injected database service.

        Returns:
            The database controller instance

        Raises:
            RuntimeError: If the database service is not available
        """
        if self.db_service is None:
            error_msg = "Database service not injected. DI is required."
            raise RuntimeError(error_msg)
        return self.db_service

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with service injection support.

        Args:
            key: The configuration key to retrieve
            default: Default value if key is not found

        Returns:
            The configuration value or default

        This method uses the injected config service only.
        """
        if self.config_service is None:
            error_msg = "Config service not injected. DI is required."
            raise RuntimeError(error_msg)
        return self.config_service.get(key, default)

    def get_bot_latency(self) -> float:
        """Get the bot's latency with service injection support.

        Returns:
            The bot's latency in seconds

        This method uses the injected bot service only.
        """
        if self.bot_service is None:
            error_msg = "Bot service not injected. DI is required."
            raise RuntimeError(error_msg)
        return self.bot_service.latency

    def get_bot_user(self, user_id: int) -> Any:
        """Get a user by ID with service injection support.

        Args:
            user_id: The Discord user ID

        Returns:
            The user object if found, None otherwise

        This method uses the injected bot service only.
        """
        if self.bot_service is None:
            error_msg = "Bot service not injected. DI is required."
            raise RuntimeError(error_msg)
        return self.bot_service.get_user(user_id)

    def get_bot_emoji(self, emoji_id: int) -> Any:
        """Get an emoji by ID with service injection support.

        Args:
            emoji_id: The Discord emoji ID

        Returns:
            The emoji object if found, None otherwise

        This method uses the injected bot service only.
        """
        if self.bot_service is None:
            error_msg = "Bot service not injected. DI is required."
            raise RuntimeError(error_msg)
        return self.bot_service.get_emoji(emoji_id)

    async def execute_database_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a database query with service injection support.

        Args:
            operation: The operation name to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the database operation

        This method uses the injected database service only.
        """
        if self.db_service is None:
            error_msg = "Database service not injected. DI is required."
            raise RuntimeError(error_msg)
        # For now, just return None since execute_query expects a callable
        # This method needs to be refactored to use proper database operations
        return None

    def __repr__(self) -> str:
        """Return a string representation of the cog."""
        # Container is required by design; reflect presence based on attribute existence
        has_container = hasattr(self, "_container")
        injection_status = "injected" if has_container else "fallback"
        bot_user = getattr(self.bot, "user", "Unknown")
        return f"<{self.__class__.__name__} bot={bot_user} injection={injection_status}>"
