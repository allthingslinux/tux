"""Unit tests for the service container."""

import pytest

from tux.core.container import (
    ServiceContainer,
    ServiceDescriptor,
    ServiceLifetime,
    ServiceRegistrationError,
    ServiceResolutionError,
)


class SimpleService:
    """Simple service for testing."""

    def __init__(self) -> None:
        self.value = "simple"


class DependentService:
    """Service with dependencies for testing."""

    def __init__(self, simple: SimpleService) -> None:
        self.simple = simple
        self.value = "dependent"


class CircularServiceA:
    """Service for testing circular dependencies."""

    def __init__(self, service_b: "CircularServiceB") -> None:
        self.service_b = service_b


class CircularServiceB:
    """Service for testing circular dependencies."""

    def __init__(self, service_a: CircularServiceA) -> None:
        self.service_a = service_a


class TestServiceContainer:
    """Test cases for ServiceContainer."""

    def test_register_singleton(self) -> None:
        """Test singleton service registration."""
        container = ServiceContainer()

        result = container.register_singleton(SimpleService)

        assert result is container  # Should return self for chaining
        assert container.is_registered(SimpleService)

        descriptor = container._services[SimpleService]
        assert descriptor.service_type == SimpleService
        assert descriptor.implementation_type == SimpleService
        assert descriptor.lifetime == ServiceLifetime.SINGLETON

    def test_register_singleton_with_implementation(self) -> None:
        """Test singleton registration with separate implementation."""
        container = ServiceContainer()

        class IService:
            pass

        class ServiceImpl(IService):
            pass

        container.register_singleton(IService, ServiceImpl)

        assert container.is_registered(IService)
        descriptor = container._services[IService]
        assert descriptor.service_type == IService
        assert descriptor.implementation_type == ServiceImpl

    def test_register_transient(self) -> None:
        """Test transient service registration."""
        container = ServiceContainer()

        container.register_transient(SimpleService)

        assert container.is_registered(SimpleService)
        descriptor = container._services[SimpleService]
        assert descriptor.lifetime == ServiceLifetime.TRANSIENT

    def test_register_instance(self) -> None:
        """Test instance service registration."""
        container = ServiceContainer()
        instance = SimpleService()

        container.register_instance(SimpleService, instance)

        assert container.is_registered(SimpleService)
        descriptor = container._services[SimpleService]
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.instance is instance

    def test_duplicate_registration_raises_error(self) -> None:
        """Test that duplicate registration raises an error."""
        container = ServiceContainer()
        container.register_singleton(SimpleService)

        with pytest.raises(ServiceRegistrationError, match="already registered"):
            container.register_singleton(SimpleService)

    def test_get_singleton_returns_same_instance(self) -> None:
        """Test that singleton services return the same instance."""
        container = ServiceContainer()
        container.register_singleton(SimpleService)

        instance1 = container.get(SimpleService)
        instance2 = container.get(SimpleService)

        assert instance1 is instance2
        assert isinstance(instance1, SimpleService)

    def test_get_transient_returns_different_instances(self) -> None:
        """Test that transient services return different instances."""
        container = ServiceContainer()
        container.register_transient(SimpleService)

        instance1 = container.get(SimpleService)
        instance2 = container.get(SimpleService)

        assert instance1 is not instance2
        assert isinstance(instance1, SimpleService)
        assert isinstance(instance2, SimpleService)

    def test_get_registered_instance(self) -> None:
        """Test getting a pre-registered instance."""
        container = ServiceContainer()
        original_instance = SimpleService()
        container.register_instance(SimpleService, original_instance)

        retrieved_instance = container.get(SimpleService)

        assert retrieved_instance is original_instance

    def test_dependency_injection(self) -> None:
        """Test automatic dependency injection."""
        container = ServiceContainer()
        container.register_singleton(SimpleService)
        container.register_singleton(DependentService)

        dependent = container.get(DependentService)

        assert isinstance(dependent, DependentService)
        assert isinstance(dependent.simple, SimpleService)
        assert dependent.value == "dependent"
        assert dependent.simple.value == "simple"

    def test_get_unregistered_service_raises_error(self) -> None:
        """Test that getting an unregistered service raises an error."""
        container = ServiceContainer()

        with pytest.raises(ServiceResolutionError, match="Cannot resolve"):
            container.get(SimpleService)

    def test_get_optional_returns_none_for_unregistered(self) -> None:
        """Test that get_optional returns None for unregistered services."""
        container = ServiceContainer()

        result = container.get_optional(SimpleService)

        assert result is None

    def test_get_optional_returns_service_when_registered(self) -> None:
        """Test that get_optional returns service when registered."""
        container = ServiceContainer()
        container.register_singleton(SimpleService)

        result = container.get_optional(SimpleService)

        assert isinstance(result, SimpleService)

    def test_circular_dependency_detection(self) -> None:
        """Test that circular dependencies are detected and raise an error."""
        container = ServiceContainer()
        container.register_singleton(CircularServiceA)
        container.register_singleton(CircularServiceB)

        with pytest.raises(ServiceResolutionError, match="Cannot resolve"):
            container.get(CircularServiceA)

    def test_is_registered(self) -> None:
        """Test the is_registered method."""
        container = ServiceContainer()

        assert not container.is_registered(SimpleService)

        container.register_singleton(SimpleService)

        assert container.is_registered(SimpleService)

    def test_method_chaining(self) -> None:
        """Test that registration methods support chaining."""
        container = ServiceContainer()

        class AnotherService:
            pass

        instance = AnotherService()

        result = (
            container
            .register_singleton(SimpleService)
            .register_transient(DependentService)
            .register_instance(AnotherService, instance)
        )

        assert result is container
        assert container.is_registered(SimpleService)
        assert container.is_registered(DependentService)
        assert container.is_registered(AnotherService)


class TestServiceDescriptor:
    """Test cases for ServiceDescriptor."""

    def test_service_descriptor_creation(self) -> None:
        """Test ServiceDescriptor creation."""
        descriptor = ServiceDescriptor(
            service_type=SimpleService,
            implementation_type=SimpleService,
            lifetime=ServiceLifetime.SINGLETON,
        )

        assert descriptor.service_type == SimpleService
        assert descriptor.implementation_type == SimpleService
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.factory is None
        assert descriptor.instance is None


class TestServiceLifetime:
    """Test cases for ServiceLifetime enum."""

    def test_service_lifetime_values(self) -> None:
        """Test ServiceLifetime enum values."""
        assert ServiceLifetime.SINGLETON.value == "singleton"
        assert ServiceLifetime.TRANSIENT.value == "transient"
        assert ServiceLifetime.SCOPED.value == "scoped"
