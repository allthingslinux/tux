"""Enhanced base cog with automatic dependency injection support.

This module provides the BaseCog class that automatically injects services
while maintaining backward compatibility with existing cog patterns.
"""

import asyncio
from typing import TYPE_CHECKING, Any

from discord.ext import commands
from loguru import logger

from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.database.controllers import DatabaseController
from tux.utils.config import Config

if TYPE_CHECKING:
    from tux.bot import Tux


class BaseCog(commands.Cog):
    """Enhanced base cog class with automatic dependency injection support.

    This class automatically injects services through the dependency injection
    contaiavailable, while providing fallback mechanisms for backward
    compatibility when the container is not available.

    The cog provides access to injected services through standard properties:
    - db_service: Database service for database operations
    - bot_service: Bot service for bot-related operations
    - config_service: Configuration service for accessing settings

    For backward compatibility, the traditional `self.db` property is also
    maintained, providing direct access to the DatabaseController.
    """

    def __init__(self, bot: "Tux") -> None:
        """Initialize the base cog with automatic service injection.

        Args:
            bot: The Tux bot instance

        The constructor attempts to inject services through the dependency
        injection container. If the container is unavailable or service
        injection fails, it falls back to direct instantiation for
        backward compatibility.
        """
        super().__init__()
        # Get the bot instance
        self.bot = bot

        # Get the container from the bot if available
        self._container = getattr(bot, "container", None)

        # Initialize service properties
        self.db_service: IDatabaseService | None = None
        self.bot_service: IBotService | None = None
        self.config_service: IConfigService | None = None

        # Backward compatibility property
        self._db_controller: DatabaseController | None = None

        # Attempt service injection
        if self._container:
            self._inject_services()
        else:
            logger.debug(f"Container not available for {self.__class__.__name__}, using fallback services")
            self._init_fallback_services()

    def _inject_services(self) -> None:
        """Inject services through the dependency injection container.

        Attempts to resolve and inject all available services. If any service
        injection fails, logs the error and falls back to direct instantiation
        for that specific service.
        """
        self._inject_database_service()
        self._inject_bot_service()
        self._inject_config_service()

    def _inject_database_service(self) -> None:
        """Inject the database service."""
        if self._container is not None:
            try:
                self.db_service = self._container.get_optional(IDatabaseService)
                if self.db_service:
                    logger.debug(f"Injected database service into {self.__class__.__name__}")
                else:
                    logger.warning(f"Database service not available for {self.__class__.__name__}, using fallback")
                    self._init_fallback_database_service()
            except Exception as e:
                logger.error(f"Database service injection failed for {self.__class__.__name__}: {e}")
                self._init_fallback_database_service()
        else:
            self._init_fallback_database_service()

    def _inject_bot_service(self) -> None:
        """Inject the bot service."""
        if self._container is not None:
            try:
                self.bot_service = self._container.get_optional(IBotService)
                if self.bot_service:
                    logger.debug(f"Injected bot service into {self.__class__.__name__}")
                else:
                    logger.warning(f"Bot service not available for {self.__class__.__name__}")
            except Exception as e:
                logger.error(f"Bot service injection failed for {self.__class__.__name__}: {e}")

    def _inject_config_service(self) -> None:
        """Inject the config service."""
        if self._container is not None:
            try:
                self.config_service = self._container.get_optional(IConfigService)
                if self.config_service:
                    logger.debug(f"Injected config service into {self.__class__.__name__}")
                else:
                    logger.warning(f"Config service not available for {self.__class__.__name__}")
            except Exception as e:
                logger.error(f"Config service injection failed for {self.__class__.__name__}: {e}")

    def _init_fallback_services(self) -> None:
        """Initialize fallback services when dependency injection is not available.

        This method provides backward compatibility by directly instantiating
        services when the dependency injection container is not available or
        service injection fails.
        """
        logger.debug(f"Initializing fallback services for {self.__class__.__name__}")

        # Initialize fallback database service
        self._init_fallback_database_service()

        # Bot service fallback is not needed as we have direct access to self.bot
        # Config service fallback is not needed as we can access Config directly

    def _init_fallback_database_service(self) -> None:
        """Initialize fallback database service by directly instantiating DatabaseController."""
        try:
            if self._db_controller is None:
                self._db_controller = DatabaseController()
                logger.debug(f"Initialized fallback database controller for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize fallback database controller for {self.__class__.__name__}: {e}")
            self._db_controller = None

    @property
    def db(self) -> DatabaseController:
        """Get the database controller for backward compatibility.

        Returns:
            The database controller instance

        This property maintains backward compatibility with existing cogs
        that access the database through `self.db`. It first attempts to
        get the controller from the injected database service, then falls
        back to the directly instantiated controller.

        Raises:
            RuntimeError: If no database controller is available
        """
        # Try to get controller from injected service first
        if self.db_service:
            try:
                return self.db_service.get_controller()
            except Exception as e:
                logger.warning(f"Failed to get controller from injected service: {e}")

        # Fall back to directly instantiated controller
        if self._db_controller is None:
            self._init_fallback_database_service()

        if self._db_controller is None:
            error_msg = f"No database controller available for {self.__class__.__name__}"
            raise RuntimeError(error_msg)

        return self._db_controller

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with service injection support.

        Args:
            key: The configuration key to retrieve
            default: Default value if key is not found

        Returns:
            The configuration value or default

        This method first attempts to use the injected config service,
        then falls back to direct Config access for backward compatibility.
        """
        # Try injected config service first
        if self.config_service:
            try:
                return self.config_service.get(key, default)
            except Exception as e:
                logger.warning(f"Failed to get config from injected service: {e}")

        # Fall back to direct Config access
        try:
            config = Config()
            return getattr(config, key) if hasattr(config, key) else default
        except Exception as e:
            logger.error(f"Failed to get config key '{key}': {e}")
            return default

    def get_bot_latency(self) -> float:
        """Get the bot's latency with service injection support.

        Returns:
            The bot's latency in seconds

        This method first attempts to use the injected bot service,
        then falls back to direct bot access for backward compatibility.
        """
        # Try injected bot service first
        if self.bot_service:
            try:
                return self.bot_service.latency
            except Exception as e:
                logger.warning(f"Failed to get latency from injected service: {e}")

        # Fall back to direct bot access
        return self.bot.latency

    def get_bot_user(self, user_id: int) -> Any:
        """Get a user by ID with service injection support.

        Args:
            user_id: The Discord user ID

        Returns:
            The user object if found, None otherwise

        This method first attempts to use the injected bot service,
        then falls back to direct bot access for backward compatibility.
        """
        # Try injected bot service first
        if self.bot_service:
            try:
                return self.bot_service.get_user(user_id)
            except Exception as e:
                logger.warning(f"Failed to get user from injected service: {e}")

        # Fall back to direct bot access
        return self.bot.get_user(user_id)

    def get_bot_emoji(self, emoji_id: int) -> Any:
        """Get an emoji by ID with service injection support.

        Args:
            emoji_id: The Discord emoji ID

        Returns:
            The emoji object if found, None otherwise

        This method first attempts to use the injected bot service,
        then falls back to direct bot access for backward compatibility.
        """
        # Try injected bot service first
        if self.bot_service:
            try:
                return self.bot_service.get_emoji(emoji_id)
            except Exception as e:
                logger.warning(f"Failed to get emoji from injected service: {e}")

        # Fall back to direct bot access
        return self.bot.get_emoji(emoji_id)

    async def execute_database_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a database query with service injection support.

        Args:
            operation: The operation name to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the database operation

        This method first attempts to use the injected database service,
        then falls back to direct controller access for backward compatibility.
        """
        # Try injected database service first
        if self.db_service:
            try:
                return await self.db_service.execute_query(operation, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to execute query through injected service: {e}")

        # Fall back to direct controller access
        controller = self.db
        if hasattr(controller, operation):
            method = getattr(controller, operation)
            if callable(method):
                if asyncio.iscoroutinefunction(method):
                    return await method(*args, **kwargs)
                return method(*args, **kwargs)
            return method
        error_msg = f"DatabaseController has no operation '{operation}'"
        raise AttributeError(error_msg)

    def __repr__(self) -> str:
        """Return a string representation of the cog."""
        injection_status = "injected" if self._container else "fallback"
        return f"<{self.__class__.__name__} bot={self.bot.user} injection={injection_status}>"
