"""Service container implementation for dependency injection.

This module provides a lightweight dependency injection container that manages
service lifecycles and resolves dependencies automatically through constructor injection.
"""

import inspect
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar, get_type_hints

from loguru import logger

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Enumeration of service lifetimes supported by the container."""

    SINGLETON = "singleton"  # One instance per container
    TRANSIENT = "transient"  # New instance per request
    SCOPED = "scoped"  # One instance per scope (future implementation)


@dataclass
class ServiceDescriptor:
    """Describes how a service should be registered and instantiated."""

    service_type: type
    implementation_type: type
    lifetime: ServiceLifetime
    factory: Callable[[], Any] | None = None
    instance: Any | None = None


class ServiceRegistrationError(Exception):
    """Raised when service registration fails."""


class ServiceResolutionError(Exception):
    """Raised when service resolution fails."""


class ServiceContainer:
    """Lightweight dependency injection container.

    Manages service lifecycles and resolves dependencies automatically through
    constructor injection. Supports singleton, transient, and scoped lifetimes.
    """

    def __init__(self) -> None:
        """Initialize an empty service container."""
        self._services: dict[type, ServiceDescriptor] = {}
        self._singleton_instances: dict[type, Any] = {}
        self._resolution_stack: set[type] = set()

    def register_singleton(self, service_type: type[T], implementation: type[T] | None = None) -> "ServiceContainer":
        """Register a service as a singleton.

        Args:
            service_type: The service interface or type to register
            implementation: The concrete implementation type (defaults to service_type)

        Returns:
            Self for method chaining

        Raises:
            ServiceRegistrationError: If registration fails
        """
        impl_type = implementation or service_type

        if service_type in self._services:
            error_msg = f"Service {service_type.__name__} is already registered"
            raise ServiceRegistrationError(error_msg)

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SINGLETON,
        )

        self._services[service_type] = descriptor
        logger.debug(f"Registered singleton service: {service_type.__name__} -> {impl_type.__name__}")

        return self

    def register_transient(self, service_type: type[T], implementation: type[T] | None = None) -> "ServiceContainer":
        """Register a service as transient (new instance per request).

        Args:
            service_type: The service interface or type to register
            implementation: The concrete implementation type (defaults to service_type)

        Returns:
            Self for method chaining

        Raises:
            ServiceRegistrationError: If registration fails
        """
        impl_type = implementation or service_type

        if service_type in self._services:
            error_msg = f"Service {service_type.__name__} is already registered"
            raise ServiceRegistrationError(error_msg)

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.TRANSIENT,
        )

        self._services[service_type] = descriptor
        logger.debug(f"Registered transient service: {service_type.__name__} -> {impl_type.__name__}")

        return self

    def register_instance(self, service_type: type[T], instance: T) -> "ServiceContainer":
        """Register a specific instance as a singleton service.

        Args:
            service_type: The service interface or type to register
            instance: The specific instance to register

        Returns:
            Self for method chaining

        Raises:
            ServiceRegistrationError: If registration fails
        """
        if service_type in self._services:
            error_msg = f"Service {service_type.__name__} is already registered"
            raise ServiceRegistrationError(error_msg)

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=type(instance),
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
        )

        self._services[service_type] = descriptor
        self._singleton_instances[service_type] = instance
        logger.debug(f"Registered instance service: {service_type.__name__}")

        return self

    def get(self, service_type: type[T]) -> T:
        """Get a service instance from the container.

        Args:
            service_type: The service type to resolve

        Returns:
            The resolved service instance

        Raises:
            ServiceResolutionError: If service resolution fails
        """
        start_time = time.perf_counter()

        try:
            result = self._resolve_service(service_type)
        except Exception as e:
            logger.error(f"Failed to resolve {service_type.__name__}: {e}")
            error_msg = f"Cannot resolve {service_type.__name__}"
            raise ServiceResolutionError(error_msg) from e
        else:
            resolution_time = time.perf_counter() - start_time
            # Only log if resolution takes longer than expected or fails
            if resolution_time > 0.001:  # Log if takes more than 1ms
                logger.debug(f"Slow resolution: {service_type.__name__} took {resolution_time:.4f}s")
            return result

    def get_optional(self, service_type: type[T]) -> T | None:
        """Get a service instance from the container, returning None if not registered.

        Args:
            service_type: The service type to resolve

        Returns:
            The resolved service instance or None if not registered
        """
        try:
            return self.get(service_type)
        except ServiceResolutionError:
            logger.debug(f"Service {service_type.__name__} not registered, returning None")
            return None

    def is_registered(self, service_type: type[T]) -> bool:
        """Check if a service type is registered in the container.

        Args:
            service_type: The service type to check

        Returns:
            True if the service is registered, False otherwise
        """
        return service_type in self._services

    def get_registered_service_types(self) -> list[type]:
        """Get a list of all registered service types.

        Returns:
            List of registered service types
        """
        return list(self._services.keys())

    def _resolve_service(self, service_type: type[T]) -> T:
        """Internal method to resolve a service instance.

        Args:
            service_type: The service type to resolve

        Returns:
            The resolved service instance

        Raises:
            ServiceResolutionError: If service resolution fails
        """
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            error_msg = f"Circular dependency detected for {service_type.__name__}"
            raise ServiceResolutionError(error_msg)

        # Check if service is registered
        if service_type not in self._services:
            error_msg = f"Service {service_type.__name__} is not registered"
            raise ServiceResolutionError(error_msg)

        descriptor = self._services[service_type]

        # Return existing instance for singletons
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singleton_instances:
                return self._singleton_instances[service_type]

            # If we have a pre-registered instance, return it
            if descriptor.instance is not None:
                return descriptor.instance

        # Create new instance
        self._resolution_stack.add(service_type)

        try:
            instance = self._create_instance(descriptor)

            # Cache singleton instances
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singleton_instances[service_type] = instance

            return instance
        finally:
            self._resolution_stack.remove(service_type)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance of a service.

        Args:
            descriptor: The service descriptor

        Returns:
            The created service instance

        Raises:
            ServiceResolutionError: If instance creation fails
        """
        impl_type = descriptor.implementation_type

        # Get constructor signature
        signature = inspect.signature(impl_type.__init__)
        parameters = list(signature.parameters.values())[1:]  # Skip 'self'

        # If no parameters, create instance directly
        if not parameters:
            return impl_type()

        # Resolve constructor dependencies
        args: list[Any] = []
        kwargs: dict[str, Any] = {}

        # Get type hints for the constructor
        type_hints = get_type_hints(impl_type.__init__)

        for param in parameters:
            param_type = type_hints.get(param.name)

            if param_type is None:
                # If no type hint, check if parameter has a default value
                if param.default is not inspect.Parameter.empty:
                    continue
                error_msg = f"Cannot resolve parameter '{param.name}' for {impl_type.__name__}: no type hint provided"
                raise ServiceResolutionError(error_msg)

            # Resolve the dependency
            dependency = self._resolve_service(param_type)

            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                if param.default is inspect.Parameter.empty:
                    args.append(dependency)
                else:
                    kwargs[param.name] = dependency
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                kwargs[param.name] = dependency

        # Create the instance
        try:
            return impl_type(*args, **kwargs)
        except Exception as e:
            error_msg = f"Failed to create instance of {impl_type.__name__}: {e}"
            raise ServiceResolutionError(error_msg) from e
