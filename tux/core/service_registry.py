"""Service registry for centralized dependency injection configuration.

This module provides the ServiceRegistry class that handles the centralized
configuration of all services in the dependency injection container.
"""

from discord.ext import commands
from loguru import logger

from tux.core.container import ServiceContainer, ServiceRegistrationError
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.core.services import BotService, ConfigService, DatabaseService


class ServiceRegistry:
    """Centralized service registry for dependency injection configuration.

    This class provides static methods to configure the service container
    with all required services and their dependencies.
    """

    @staticmethod
    def configure_container(bot: commands.Bot) -> ServiceContainer:
        """Configure the service container with all core services.

        This method registers all core services with their appropriate lifetimes
        and dependencies. It serves as the central configuration point for the
        dependency injection system.

        Args:
            bot: The Discord bot instance to use for bot-dependent services

        Returns:
            A fully configured service container ready for use

        Raises:
            ServiceRegistrationError: If any service registration fails
        """
        logger.info("Starting service container configuration")

        try:
            container = ServiceContainer()

            # Register core services as singletons
            logger.debug("Registering core singleton services")

            # Database service - singleton for connection pooling and performance
            container.register_singleton(IDatabaseService, DatabaseService)
            logger.debug("Registered DatabaseService as singleton")

            # Config service - singleton for consistent configuration access
            container.register_singleton(IConfigService, ConfigService)
            logger.debug("Registered ConfigService as singleton")

            # Bot service - register as instance since we have the bot instance
            logger.debug("Registering bot-dependent services")
            bot_service = BotService(bot)
            container.register_instance(IBotService, bot_service)
            logger.debug("Registered BotService instance")

            logger.info("Service container configuration completed successfully")
            return container

        except ServiceRegistrationError as e:
            logger.error(f"Service registration failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during service registration: {e}")
            error_msg = f"Failed to configure service container: {e}"
            raise ServiceRegistrationError(error_msg) from e

    @staticmethod
    def configure_test_container() -> ServiceContainer:
        """Configure a service container for testing purposes.

        This method creates a minimal container configuration suitable for
        unit testing without requiring a full bot instance.

        Returns:
            A service container configured for testing

        Raises:
            ServiceRegistrationError: If any service registration fails
        """
        logger.debug("Configuring test service container")

        try:
            container = ServiceContainer()

            # Register only essential services for testing
            container.register_singleton(IDatabaseService, DatabaseService)
            container.register_singleton(IConfigService, ConfigService)

            logger.debug("Test service container configuration completed")
            return container

        except Exception as e:
            logger.error(f"Failed to configure test container: {e}")
            error_msg = f"Failed to configure test container: {e}"
            raise ServiceRegistrationError(error_msg) from e

    @staticmethod
    def validate_container(container: ServiceContainer) -> bool:
        """Validate that a service container has all required services registered.

        Args:
            container: The service container to validate

        Returns:
            True if all required services are registered, False otherwise
        """
        required_services = [IDatabaseService, IConfigService, IBotService]

        logger.debug("Validating service container configuration")

        for service_type in required_services:
            if not container.is_registered(service_type):
                logger.error(f"Required service {service_type.__name__} is not registered")
                return False

        logger.debug("Service container validation passed")
        return True

    @staticmethod
    def get_registered_services(container: ServiceContainer) -> list[str]:
        """Get a list of all registered service names for debugging.

        Args:
            container: The service container to inspect

        Returns:
            List of registered service type names
        """
        # Use the public method to get registered service types
        try:
            service_types = container.get_registered_service_types()
            return [service_type.__name__ for service_type in service_types]
        except AttributeError:
            # Fallback for containers that don't have the method
            return []
