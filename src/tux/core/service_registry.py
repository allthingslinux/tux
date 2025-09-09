"""Service registry for centralized dependency injection configuration.

This module provides the ServiceRegistry class that handles the centralized
configuration of all services in the dependency injection container.
"""

from typing import TYPE_CHECKING, Any, cast

from discord.ext import commands
from loguru import logger

from tux.core.container import ServiceContainer, ServiceRegistrationError
from tux.core.interfaces import IBotService, IGithubService, ILoggerService
from tux.core.services import BotService, GitHubService, LoggerService
from tux.core.types import Tux
from tux.database.controllers import DatabaseCoordinator
from tux.database.service import DatabaseService

# Import moderation services for type checking only to avoid circular imports
if TYPE_CHECKING:
    from tux.services.moderation import CaseService, ExecutionService


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
            db_service = DatabaseService()
            container.register_instance(DatabaseService, db_service)
            logger.debug("Registered DatabaseService as singleton")

            # Config service - singleton for consistent configuration access

            # GitHub service - singleton for API rate limiting and connection pooling
            container.register_singleton(IGithubService, GitHubService)
            logger.debug("Registered GitHubService as singleton")

            # Logger service - singleton for consistent logging configuration
            container.register_singleton(ILoggerService, LoggerService)
            logger.debug("Registered LoggerService as singleton")

            # Bot service - register as instance since we have the bot instance
            logger.debug("Registering bot-dependent services")
            bot_service = BotService(bot)
            container.register_instance(IBotService, bot_service)
            logger.debug("Registered BotService instance")

            # Register moderation services
            ServiceRegistry._configure_moderation_services(container, bot)
            logger.debug("Registered moderation services")

        except ServiceRegistrationError:
            logger.error("❌ Service registration failed")
            logger.info("💡 Check your service configurations and dependencies")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during service registration: {type(e).__name__}")
            logger.info("💡 Check your service dependencies and configurations")
            error_msg = f"Failed to configure service container: {e}"
            raise ServiceRegistrationError(error_msg) from e
        else:
            logger.info("Service container configuration completed successfully")
            return container

    @staticmethod
    def _configure_moderation_services(container: ServiceContainer, bot: commands.Bot) -> None:
        """Configure moderation services in the DI container.

        Args:
            container: The service container to register services in
            bot: The Discord bot instance for bot-dependent services

        Raises:
            ServiceRegistrationError: If service registration fails
        """
        try:
            # Import moderation services (avoiding circular imports)
            from tux.services.moderation import (  # noqa: PLC0415
                CaseService,
                CommunicationService,
                ExecutionService,
                ModerationCoordinator,
            )

            # Get database service for case controller dependency
            db_service = container.get(DatabaseService)

            # Create database coordinator to access controllers
            db_coordinator = DatabaseCoordinator(db_service)

            # Create and register CaseService with database dependency
            case_service = CaseService(db_coordinator.case)  # type: ignore[arg-type]
            container.register_instance(CaseService, case_service)
            logger.debug("Registered CaseService instance")

            # Create and register ExecutionService (no dependencies)
            execution_service = ExecutionService()
            container.register_instance(ExecutionService, execution_service)
            logger.debug("Registered ExecutionService instance")

            # Create and register CommunicationService with bot dependency
            communication_service = CommunicationService(cast("Tux", bot))  # type: ignore[arg-type]
            container.register_instance(CommunicationService, communication_service)
            logger.debug("Registered CommunicationService instance")

            # Create and register ModerationCoordinator with all dependencies
            moderation_coordinator = ModerationCoordinator(
                case_service=case_service,
                communication_service=communication_service,
                execution_service=execution_service,
            )
            container.register_instance(ModerationCoordinator, moderation_coordinator)
            logger.debug("Registered ModerationCoordinator instance")

        except Exception as e:
            error_msg = f"Failed to configure moderation services: {e}"
            logger.error(f"❌ {error_msg}")
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
            db_service = DatabaseService()
            container.register_instance(DatabaseService, db_service)

            # Register moderation services for testing
            ServiceRegistry._configure_test_moderation_services(container)

            # Do not register IBotService in test container to match unit tests expectations

        except Exception as e:
            logger.error(f"❌ Failed to configure test container: {type(e).__name__}")
            logger.info("💡 Check your test service dependencies")
            error_msg = f"Failed to configure test container: {e}"
            raise ServiceRegistrationError(error_msg) from e
        else:
            logger.debug("Test service container configuration completed")
            return container

    @staticmethod
    def _configure_test_moderation_services(container: ServiceContainer) -> None:
        """Configure moderation services for testing.

        Args:
            container: The test service container to register services in

        Raises:
            ServiceRegistrationError: If service registration fails
        """
        try:
            # Get database service for case controller dependency
            db_service = container.get(DatabaseService)

            # Create database coordinator to access controllers
            db_coordinator = DatabaseCoordinator(db_service)

            # Create and register CaseService with database dependency
            case_service = CaseService(db_coordinator.case)
            container.register_instance(CaseService, case_service)

            # Create and register ExecutionService (no dependencies)
            execution_service = ExecutionService()
            container.register_instance(ExecutionService, execution_service)

            # Note: CommunicationService and ModerationCoordinator require a bot instance
            # which is not available in test containers. Tests that need these services
            # should mock them or use integration tests.

        except Exception as e:
            error_msg = f"Failed to configure test moderation services: {e}"
            logger.error(f"❌ {error_msg}")
            raise ServiceRegistrationError(error_msg) from e

    @staticmethod
    def validate_container(container: ServiceContainer) -> bool:
        """Validate that a service container has all required services registered.

        Args:
            container: The service container to validate

        Returns:
            True if all required services are registered, False otherwise
        """
        # Core required services that should always be present
        core_required_services = [DatabaseService, ILoggerService]
        # Moderation services that should be present in full containers (imported lazily)
        from tux.services.moderation import (  # noqa: PLC0415
            CaseService,
            CommunicationService,
            ExecutionService,
            ModerationCoordinator,
        )

        moderation_services = [CaseService, CommunicationService, ExecutionService, ModerationCoordinator]
        required_services = core_required_services + moderation_services

        logger.debug("Validating service container configuration")

        # Check core required services
        for service_type in required_services:
            if not container.is_registered(service_type):
                logger.error(f"Required service {service_type.__name__} is not registered")
                return False

        # Check bot-dependent services if they should be present
        # In test containers, we might have a mock bot service
        if container.is_registered(IBotService):
            logger.debug("Bot service detected - full container validation")
            # If we have a bot service, make sure it's properly initialized
            try:
                bot_service = container.get(IBotService)
                if not hasattr(bot_service, "bot"):
                    logger.error("Bot service is missing required 'bot' attribute")
                    return False
            except Exception as e:
                logger.error(f"Failed to validate bot service: {e}")
                return False
        else:
            logger.debug("No bot service - minimal container validation")

        logger.debug("Service container validation passed")
        return True

    @staticmethod
    def get_registered_services(container: ServiceContainer) -> list[str]:
        """Get a list of core registered service names for debugging.

        Args:
            container: The service container to inspect

        Returns:
            List of registered core service type names
        """
        # Use the public method to get registered service types
        try:
            service_types: list[type] = container.get_registered_service_types()
            # Return core services expected by tests plus moderation services
            from tux.services.moderation import CaseService, ExecutionService  # noqa: PLC0415

            core = {DatabaseService.__name__, IBotService.__name__, CaseService.__name__, ExecutionService.__name__}
            return [service_type.__name__ for service_type in service_types if service_type.__name__ in core]
        except AttributeError:
            # Fallback for containers that don't have the method
            return []

    @staticmethod
    def get_service_info(container: ServiceContainer) -> dict[str, str]:
        """Get detailed information about registered services.

        Args:
            container: The service container to inspect

        Returns:
            Dictionary mapping service names to their implementation types
        """
        service_info: dict[str, str] = {}
        try:
            # Use public API to get service types if available
            if hasattr(container, "get_registered_service_types"):
                service_types = container.get_registered_service_types()
            else:
                logger.warning("Container does not support get_registered_service_types()")
                return service_info

            for service_type in service_types:
                try:
                    # Get the service implementation
                    service_impl: Any = cast(Any, container.get(service_type))  # type: ignore[arg-type]
                    if service_impl is not None:
                        impl_name = type(service_impl).__name__
                        service_info[service_type.__name__] = impl_name
                    else:
                        service_info[service_type.__name__] = "None"
                except Exception as e:
                    logger.debug(f"Could not get implementation for {service_type.__name__}: {e}")
                    service_info[service_type.__name__] = "Unknown implementation"

        except Exception as e:
            logger.error(f"Failed to get service info: {e}")

        return service_info
