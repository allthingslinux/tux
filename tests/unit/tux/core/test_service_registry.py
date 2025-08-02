"""Unit tests for the service registry module.

This module contains comprehensive tests for the ServiceRegistry class,
including service registration, error handling, and validation functionality.
"""

from unittest.mock import Mock, patch

import pytest

from tux.core.container import ServiceContainer, ServiceRegistrationError
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.core.service_registry import ServiceRegistry
from tux.core.services import BotService, ConfigService, DatabaseService


class TestServiceRegistry:
    """Test cases for the ServiceRegistry class."""

    def test_configure_container_success(self):
        """Test successful service container configuration."""
        # Arrange
        mock_bot = Mock()

        # Act
        container = ServiceRegistry.configure_container(mock_bot)

        # Assert
        assert isinstance(container, ServiceContainer)
        assert container.is_registered(IDatabaseService)
        assert container.is_registered(IConfigService)
        assert container.is_registered(IBotService)

    def test_configure_container_registers_correct_implementations(self):
        """Test that the correct service implementations are registered."""
        # Arrange
        mock_bot = Mock()

        # Act
        container = ServiceRegistry.configure_container(mock_bot)

        # Assert
        db_service = container.get(IDatabaseService)
        config_service = container.get(IConfigService)
        bot_service = container.get(IBotService)

        assert isinstance(db_service, DatabaseService)
        assert isinstance(config_service, ConfigService)
        assert isinstance(bot_service, BotService)

    def test_configure_container_singleton_behavior(self):
        """Test that singleton services return the same instance."""
        # Arrange
        mock_bot = Mock()
        container = ServiceRegistry.configure_container(mock_bot)

        # Act
        db_service1 = container.get(IDatabaseService)
        db_service2 = container.get(IDatabaseService)
        config_service1 = container.get(IConfigService)
        config_service2 = container.get(IConfigService)
        bot_service1 = container.get(IBotService)
        bot_service2 = container.get(IBotService)

        # Assert
        assert db_service1 is db_service2
        assert config_service1 is config_service2
        assert bot_service1 is bot_service2

    def test_configure_container_bot_service_has_correct_bot_instance(self):
        """Test that the BotService is initialized with the correct bot instance."""
        # Arrange
        mock_bot = Mock()
        mock_bot.latency = 0.123

        # Act
        container = ServiceRegistry.configure_container(mock_bot)
        bot_service = container.get(IBotService)

        # Assert
        assert bot_service.latency == 0.123

    @patch("tux.core.service_registry.ServiceContainer")
    def test_configure_container_handles_registration_error(self, mock_container_class):
        """Test error handling when service registration fails."""
        # Arrange
        mock_bot = Mock()
        mock_container = Mock()
        mock_container.register_singleton.side_effect = ServiceRegistrationError("Registration failed")
        mock_container_class.return_value = mock_container

        # Act & Assert
        with pytest.raises(ServiceRegistrationError, match="Registration failed"):
            ServiceRegistry.configure_container(mock_bot)

    @patch("tux.core.service_registry.ServiceContainer")
    def test_configure_container_handles_unexpected_error(self, mock_container_class):
        """Test error handling for unexpected errors during configuration."""
        # Arrange
        mock_bot = Mock()
        mock_container_class.side_effect = Exception("Unexpected error")

        # Act & Assert
        with pytest.raises(ServiceRegistrationError, match="Failed to configure service container"):
            ServiceRegistry.configure_container(mock_bot)

    def test_configure_test_container_success(self):
        """Test successful test container configuration."""
        # Act
        container = ServiceRegistry.configure_test_container()

        # Assert
        assert isinstance(container, ServiceContainer)
        assert container.is_registered(IDatabaseService)
        assert container.is_registered(IConfigService)
        # Bot service should not be registered in test container
        assert not container.is_registered(IBotService)

    def test_configure_test_container_registers_correct_implementations(self):
        """Test that test container registers correct implementations."""
        # Act
        container = ServiceRegistry.configure_test_container()

        # Assert
        db_service = container.get(IDatabaseService)
        config_service = container.get(IConfigService)

        assert isinstance(db_service, DatabaseService)
        assert isinstance(config_service, ConfigService)

    @patch("tux.core.service_registry.ServiceContainer")
    def test_configure_test_container_handles_error(self, mock_container_class):
        """Test error handling in test container configuration."""
        # Arrange
        mock_container_class.side_effect = Exception("Test error")

        # Act & Assert
        with pytest.raises(ServiceRegistrationError, match="Failed to configure test container"):
            ServiceRegistry.configure_test_container()

    def test_validate_container_with_all_services(self):
        """Test container validation when all required services are present."""
        # Arrange
        mock_bot = Mock()
        container = ServiceRegistry.configure_container(mock_bot)

        # Act
        result = ServiceRegistry.validate_container(container)

        # Assert
        assert result is True

    def test_validate_container_missing_database_service(self):
        """Test container validation when database service is missing."""
        # Arrange
        container = ServiceContainer()
        container.register_singleton(IConfigService, ConfigService)
        container.register_instance(IBotService, BotService(Mock()))

        # Act
        result = ServiceRegistry.validate_container(container)

        # Assert
        assert result is False

    def test_validate_container_missing_config_service(self):
        """Test container validation when config service is missing."""
        # Arrange
        container = ServiceContainer()
        container.register_singleton(IDatabaseService, DatabaseService)
        container.register_instance(IBotService, BotService(Mock()))

        # Act
        result = ServiceRegistry.validate_container(container)

        # Assert
        assert result is False

    def test_validate_container_missing_bot_service(self):
        """Test container validation when bot service is missing."""
        # Arrange
        container = ServiceContainer()
        container.register_singleton(IDatabaseService, DatabaseService)
        container.register_singleton(IConfigService, ConfigService)

        # Act
        result = ServiceRegistry.validate_container(container)

        # Assert
        assert result is False

    def test_validate_container_empty_container(self):
        """Test container validation with empty container."""
        # Arrange
        container = ServiceContainer()

        # Act
        result = ServiceRegistry.validate_container(container)

        # Assert
        assert result is False

    def test_get_registered_services_with_services(self):
        """Test getting registered service names from configured container."""
        # Arrange
        mock_bot = Mock()
        container = ServiceRegistry.configure_container(mock_bot)

        # Act
        service_names = ServiceRegistry.get_registered_services(container)

        # Assert
        assert "IDatabaseService" in service_names
        assert "IConfigService" in service_names
        assert "IBotService" in service_names
        assert len(service_names) == 3

    def test_get_registered_services_empty_container(self):
        """Test getting registered service names from empty container."""
        # Arrange
        container = ServiceContainer()

        # Act
        service_names = ServiceRegistry.get_registered_services(container)

        # Assert
        assert service_names == []

    def test_get_registered_services_no_services_attribute(self):
        """Test getting registered service names when container has no get_registered_service_types method."""
        # Arrange
        mock_container = Mock()
        mock_container.get_registered_service_types.side_effect = AttributeError("Method not found")

        # Act
        service_names = ServiceRegistry.get_registered_services(mock_container)

        # Assert
        assert service_names == []


class TestServiceRegistryIntegration:
    """Integration tests for ServiceRegistry with real service instances."""

    def test_full_container_configuration_and_usage(self):
        """Test complete container configuration and service usage."""
        # Arrange
        mock_bot = Mock()
        mock_bot.latency = 0.456
        mock_bot.get_user.return_value = Mock()

        # Act
        container = ServiceRegistry.configure_container(mock_bot)

        # Get all services
        db_service = container.get(IDatabaseService)
        config_service = container.get(IConfigService)
        bot_service = container.get(IBotService)

        # Assert services are functional
        assert db_service.get_controller() is not None
        assert bot_service.latency == 0.456
        assert config_service.is_dev_mode() in [True, False]  # Should return a boolean

    def test_container_validation_after_configuration(self):
        """Test that configured container passes validation."""
        # Arrange
        mock_bot = Mock()

        # Act
        container = ServiceRegistry.configure_container(mock_bot)
        is_valid = ServiceRegistry.validate_container(container)

        # Assert
        assert is_valid is True

    def test_test_container_configuration_and_validation(self):
        """Test test container configuration and partial validation."""
        # Act
        container = ServiceRegistry.configure_test_container()

        # Assert essential services are present
        assert container.is_registered(IDatabaseService)
        assert container.is_registered(IConfigService)

        # Bot service should not be present in test container
        assert not container.is_registered(IBotService)

        # Validation should fail because bot service is missing
        is_valid = ServiceRegistry.validate_container(container)
        assert is_valid is False
