"""Lightweight dependency injection container for Tux bot."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar, get_type_hints

from loguru import logger

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Service lifetime enumeration."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(
        self,
        service_type: type,
        lementation_type: type,
        lifetime: ServiceLifetime,
        factory: Callable[..., Any] | None = None,
        instance: Any = None,
    ) -> None:
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.lifetime = lifetime
        self.factory = factory
        self.instance = instance


class ServiceContainer:
    """Lightweight dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type, ServiceDescriptor] = {}
        self._singletons: dict[type, Any] = {}
        self._scoped_instances: dict[type, Any] = {}

    def register_singleton(self, service_type: type[T], implementation: type[T] | None = None) -> ServiceContainer:
        """
        Register a service as singleton.

        Parameters
        ----------
        service_type : type[T]
            The service interface or type to register.
        implementation : type[T] | None
            The implementation type. If None, uses service_type.

        Returns
        -------
        ServiceContainer
            Self for method chaining.
        """
        impl_type = implementation or service_type
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SINGLETON,
        )
        logger.debug(f"Registered singleton service: {service_type.__name__} -> {impl_type.__name__}")
        return self

    def register_transient(self, service_type: type[T], implementation: type[T] | None = None) -> ServiceContainer:
        """
        Register a service as transient.

        Parameters
        ----------
        service_type : type[T]
            The service interface or type to register.
        implementation : type[T] | None
            The implementation type. If None, uses service_type.

        Returns
        -------
        ServiceContainer
            Self for method chaining.
        """
        impl_type = implementation or service_type
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.TRANSIENT,
        )
        logger.debug(f"Registered transient service: {service_type.__name__} -> {impl_type.__name__}")
        return self

    def register_scoped(self, service_type: type[T], implementation: type[T] | None = None) -> ServiceContainer:
        """
        Register a service as scoped.

        Parameters
        ----------
        service_type : type[T]
            The service interface or type to register.
        implementation : type[T] | None
            The implementation type. If None, uses service_type.

        Returns
        -------
        ServiceContainer
            Self for method chaining.
        """
        impl_type = implementation or service_type
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SCOPED,
        )
        logger.debug(f"Registered scoped service: {service_type.__name__} -> {impl_type.__name__}")
        return self

    def register_instance(self, service_type: type[T], instance: T) -> ServiceContainer:
        """
        Register a specific instance.

        Parameters
        ----------
        service_type : type[T]
            The service type to register.
        instance : T
            The instance to register.

        Returns
        -------
        ServiceContainer
            Self for method chaining.
        """
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=type(instance),
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
        )
        self._singletons[service_type] = instance
        logger.debug(f"Registered instance: {service_type.__name__}")
        return self

    def register_factory(
        self,
        service_type: type[T],
        factory: Callable[..., T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> ServiceContainer:
        """
        Register a factory function for creating service instances.

        Parameters
        ----------
        service_type : type[T]
            The service type to register.
        factory : Callable[..., T]
            The factory function.
        lifetime : ServiceLifetime
            The service lifetime.

        Returns
        -------
        ServiceContainer
            Self for method chaining.
        """
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=service_type,
            lifetime=lifetime,
            factory=factory,
        )
        logger.debug(f"Registered factory for: {service_type.__name__}")
        return self

    def get(self, service_type: type[T]) -> T:
        """
        Get a service instance.

        Parameters
        ----------
        service_type : type[T]
            The service type to retrieve.

        Returns
        -------
        T
            The service instance.

        Raises
        ------
        ValueError
            If the service is not registered.
        """
        if service_type not in self._services:
            msg = f"Service {service_type.__name__} is not registered"
            raise ValueError(msg)

        descriptor = self._services[service_type]

        # Return existing instance if it's a singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]

        # Return existing scoped instance
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]

        # Create new instance
        instance = self._create_instance(descriptor)

        # Store singleton instances
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            self._singletons[service_type] = instance

        # Store scoped instances
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            self._scoped_instances[service_type] = instance

        return instance

    def get_optional(self, service_type: type[T]) -> T | None:
        """
        Get a service instance or None if not registered.

        Parameters
        ----------
        service_type : type[T]
            The service type to retrieve.

        Returns
        -------
        T | None
            The service instance or None.
        """
        try:
            return self.get(service_type)
        except ValueError:
            return None

    def clear_scoped(self) -> None:
        """Clear all scoped service instances."""
        self._scoped_instances.clear()
        logger.debug("Cleared scoped service instances")

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """
        Create a service instance from a descriptor.

        Parameters
        ----------
        descriptor : ServiceDescriptor
            The service descriptor.

        Returns
        -------
        Any
            The created instance.
        """
        # Use existing instance if available
        if descriptor.instance is not None:
            return descriptor.instance

        # Use factory if available
        if descriptor.factory is not None:
            return self._invoke_factory(descriptor.factory)

        # Create instance using constructor injection
        return self._create_with_injection(descriptor.implementation_type)

    def _invoke_factory(self, factory: Callable[..., Any]) -> Any:
        """
        Invoke a factory function with dependency injection.

        Parameters
        ----------
        factory : Callable[..., Any]
            The factory function.

        Returns
        -------
        Any
            The created instance.
        """
        sig = inspect.signature(factory)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                dependency = self.get_optional(param.annotation)
                if dependency is not None:
                    kwargs[param_name] = dependency

        return factory(**kwargs)

    def _create_with_injection(self, implementation_type: type) -> Any:
        """
        Create an instance using constructor dependency injection.

        Parameters
        ----------
        implementation_type : type
            The type to instantiate.

        Returns
        -------
        Any
            The created instance.
        """
        try:
            # Get constructor signature
            sig = inspect.signature(implementation_type.__init__)
            type_hints = get_type_hints(implementation_type.__init__)

            kwargs = {}

            # Resolve dependencies for each parameter
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Try to get type from type hints first, then from annotation
                param_type = type_hints.get(param_name, param.annotation)

                if param_type != inspect.Parameter.empty:
                    dependency = self.get_optional(param_type)
                    if dependency is not None:
                        kwargs[param_name] = dependency
                    elif param.default == inspect.Parameter.empty:
                        # Required parameter without default value
                        logger.warning(
                            f"Cannot resolve required dependency {param_name}: {param_type} "
                            f"for {implementation_type.__name__}"
                        )

            return implementation_type(**kwargs)

        except Exception as e:
            logger.error(f"Failed to create instance of {implementation_type.__name__}: {e}")
            # Fallback to parameterless constructor
            try:
                return implementation_type()
            except Exception as fallback_error:
                logger.error(f"Fallback constructor also failed for {implementation_type.__name__}: {fallback_error}")
                raise

    def get_registered_services(self) -> dict[type, ServiceDescriptor]:
        """
        Get all registered services.

        Returns
        -------
        dict[type, ServiceDescriptor]
            Dictionary of registered services.
        """
        return self._services.copy()

    def is_registered(self, service_type: type) -> bool:
        """
        Check if a service type is registered.

        Parameters
        ----------
        service_type : type
            The service type to check.

        Returns
        -------
        bool
            True if registered, False otherwise.
        """
        return service_type in self._services
