"""Service registration for the Tux bot dependency injection container."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from tux.core.container import ServiceContainer
from tux.core.interfaces import (
    IConfigurationService,
    IDatabaseService,
    IEmbedService,
    IExternalAPIService,
    ILoggingService,
    IServiceContainer,
)
from tux.core.services import (
    ConfigurationService,
    DatabaseService,
    EmbedService,
    GitHubAPIService,
    LoggingService,
)

if TYPE_CHECKING:
    from tux.bot import Tux


class ServiceRegistry:
    """Handles service registration for the dependency injection container."""

    @staticmethod
    def register_core_services(container: ServiceContainer, bot: Tux) -> None:
        """
        Register core services in the container.

        Parameters
        ----------
        container : ServiceContainer
            The service container to register services in.
        bot : Tux
            The bot instance.
        """
        logger.info("Registering core services...")

        # Register the container itself
        container.register_instance(IServiceContainer, container)
        container.register_instance(ServiceContainer, container)

        # Register core services as singletons
        container.register_singleton(IDatabaseService, DatabaseService)
        container.register_singleton(IConfigurationService, ConfigurationService)
        container.register_singleton(IExternalAPIService, GitHubAPIService)
        container.register_singleton(ILoggingService, LoggingService)

        # Register embed service with bot dependency
        container.register_factory(
            IEmbedService,
            lambda: EmbedService(bot),
        )

        # Register bot instance
        container.register_instance(type(bot), bot)

        logger.info("Core services registered successfully")

    @staticmethod
    def register_cog_services(container: ServiceContainer) -> None:
        """
        Register cog-specific services.

        Parameters
        ----------
        container : ServiceContainer
            The service container to register services in.
        """
        logger.info("Registering cog services...")

        # Add cog-specific service registrations here as needed
        # For example:
        # container.register_transient(ISomeSpecificService, SomeSpecificService)

        logger.info("Cog services registered successfully")

    @staticmethod
    def configure_container(bot: Tux) -> ServiceContainer:
        """
        Configure and return a fully set up service container.

        Parameters
        ----------
        bot : Tux
            The bot instance.

        Returns
        -------
        ServiceContainer
            The configured service container.
        """
        container = ServiceContainer()

        try:
            ServiceRegistry.register_core_services(container, bot)
            ServiceRegistry.register_cog_services(container)

            logger.info("Service container configured successfully")
            return container

        except Exception as e:
            logger.error(f"Failed to configure service container: {e}")
            raise
