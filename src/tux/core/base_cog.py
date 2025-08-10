"""Enhanced base cog with automatic dependency injection support.

This module provides the `BaseCog` class that automatically injects services
via the dependency injection container. Backward-compatibility fallbacks have
been removed; cogs are expected to run with a configured service container.
"""

from typing import TYPE_CHECKING, Any

from discord.ext import commands
from loguru import logger

from tux.core.interfaces import IBotService, IConfigService, IDatabaseService

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
    """

    def __init__(self, bot: "Tux") -> None:
        """Initialize the base cog with automatic service injection.

        Args:
            bot: The Tux bot instance

        The constructor injects services through the dependency injection
        container. The container is required; no fallbacks are provided.
        """
        super().__init__()
        # Initialize service properties first
        self.db_service: IDatabaseService | None = None
        self.bot_service: IBotService | None = None
        self.config_service: IConfigService | None = None
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

    def _inject_services(self) -> None:
        """Inject services through the dependency injection container.

        Attempts to resolve and inject all available services. If any service
        injection fails, it will be logged; no legacy fallbacks are provided.
        """
        logger.debug(f"[BaseCog] Starting service injection for {self.__class__.__name__}")
        logger.debug(f"[BaseCog] Has container: {hasattr(self, '_container')}")

        logger.debug(f"[BaseCog] Container type: {type(self._container).__name__}")
        logger.debug(f"[BaseCog] Container state: {self._container}")

        # Inject services in order of dependency
        self._inject_database_service()
        self._inject_bot_service()
        self._inject_config_service()

        logger.debug(f"[BaseCog] Completed service injection for {self.__class__.__name__}")
        logger.debug(
            f"[BaseCog] Services - db_service: {self.db_service is not None}, "
            f"bot_service: {self.bot_service is not None}, "
            f"config_service: {self.config_service is not None}",
        )

    def _inject_database_service(self) -> None:
        """Inject the database service."""
        try:
            self.db_service = self._container.get_optional(IDatabaseService)
            if self.db_service:
                logger.debug(f"Injected database service into {self.__class__.__name__}")
            else:
                logger.warning(f"Database service not available for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Database service injection failed for {self.__class__.__name__}: {e}")

    def _inject_bot_service(self) -> None:
        """Inject the bot service."""
        logger.debug(f"[BaseCog] Attempting to inject bot service for {self.__class__.__name__}")

        logger.debug("[BaseCog] Container is available, trying to get IBotService")
        try:
            logger.debug("[BaseCog] Calling container.get_optional(IBotService)")
            self.bot_service = self._container.get_optional(IBotService)
            logger.debug(f"[BaseCog] container.get_optional(IBotService) returned: {self.bot_service}")

            if self.bot_service:
                logger.debug(f"[BaseCog] Successfully injected bot service into {self.__class__.__name__}")
                logger.debug(f"[BaseCog] Bot service type: {type(self.bot_service).__name__}")
            else:
                logger.warning(
                    f"[BaseCog] Bot service not available for {self.__class__.__name__} (container returned None)",
                )
        except Exception as e:
            logger.error(f"[BaseCog] Bot service injection failed for {self.__class__.__name__}: {e}", exc_info=True)

    def _inject_config_service(self) -> None:
        """Inject the config service."""
        try:
            self.config_service = self._container.get_optional(IConfigService)
            if self.config_service:
                logger.debug(f"Injected config service into {self.__class__.__name__}")
            else:
                logger.warning(f"Config service not available for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Config service injection failed for {self.__class__.__name__}: {e}")

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
        return self.db_service.get_controller()

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
        return await self.db_service.execute_query(operation, *args, **kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the cog."""
        # Container is required by design; reflect presence based on attribute existence
        has_container = hasattr(self, "_container")
        injection_status = "injected" if has_container else "fallback"
        bot_user = getattr(self.bot, "user", "Unknown")
        return f"<{self.__class__.__name__} bot={bot_user} injection={injection_status}>"
