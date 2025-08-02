"""Unit tests for the BaseCog class with dependency injection support."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.container import ServiceContainer
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.database.controllers import DatabaseController


class MockDatabaseService:
    """Mock database service for testing."""

    def __init__(self):
        self.controller = Mock(spec=DatabaseController)

    def get_controller(self):
        return self.controller

    async def execute_query(self, operation, *args, **kwargs):
        return f"mock_result_{operation}"


class MockBotService:
    """Mock bot service for testing."""

    def __init__(self):
        self.latency = 0.123
        self._users = {}
        self._emojis = {}

    def get_user(self, user_id):
        return self._users.get(user_id)

    def get_emoji(self, emoji_id):
        return self._emojis.get(emoji_id)


class MockConfigService:
    """Mock config service for testing."""

    def __init__(self):
        self._config = {"test_key": "test_value", "bot_token": "mock_token"}

    def get(self, key, default=None):
        return self._config.get(key, default)


class TestBaseCog:
    """Test cases for BaseCog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = Mock()
        bot.latency = 0.456
        bot.get_user = Mock(return_value=None)
        bot.get_emoji = Mock(return_value=None)
        return bot

    @pytest.fixture
    def mock_container(self):
        """Create a mock service container with registered services."""
        container = Mock(spec=ServiceContainer)

        # Mock services
        db_service = MockDatabaseService()
        bot_service = MockBotService()
        config_service = MockConfigService()

        # Configure container to return services
        def get_optional_side_effect(service_type):
            if service_type == IDatabaseService:
                return db_service
            elif service_type == IBotService:
                return bot_service
            elif service_type == IConfigService:
                return config_service
            return None

        container.get_optional.side_effect = get_optional_side_effect
        return container

    @pytest.fixture
    def mock_bot_with_container(self, mock_bot, mock_container):
        """Create a mock bot with dependency injection container."""
        mock_bot.container = mock_container
        return mock_bot

    @pytest.fixture
    def mock_bot_without_container(self):
        """Create a mock bot without dependency injection container."""
        bot = Mock()
        bot.latency = 0.456
        bot.get_user = Mock(return_value=None)
        bot.get_emoji = Mock(return_value=None)
        # Ensure no container attribute
        if hasattr(bot, 'container'):
            delattr(bot, 'container')
        return bot

    def test_init_with_container_successful_injection(self, mock_bot_with_container):
        """Test BaseCog initialization with successful service injection."""
        cog = BaseCog(mock_bot_with_container)

        # Verify bot is set
        assert cog.bot == mock_bot_with_container

        # Verify container is available
        assert cog._container == mock_bot_with_container.container

        # Verify services are injected
        assert cog.db_service is not None
        assert cog.bot_service is not None
        assert cog.config_service is not None

        # Verify container was called for each service
        assert mock_bot_with_container.container.get_optional.call_count == 3

    def test_init_without_container_fallback(self, mock_bot_without_container):
        """Test BaseCog initialization without container falls back correctly."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_db_controller.return_value = Mock(spec=DatabaseController)

            cog = BaseCog(mock_bot_without_container)

            # Verify bot is set
            assert cog.bot == mock_bot_without_container

            # Verify no container
            assert cog._container is None

            # Verify services are None (fallback mode)
            assert cog.db_service is None
            assert cog.bot_service is None
            assert cog.config_service is None

            # Verify fallback database controller was created
            mock_db_controller.assert_called_once()

    def test_init_with_container_injection_failure(self, mock_bot_with_container):
        """Test BaseCog initialization handles service injection failures gracefully."""
        # Make container.get_optional raise an exception
        mock_bot_with_container.container.get_optional.side_effect = Exception("Injection failed")

        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_db_controller.return_value = Mock(spec=DatabaseController)

            cog = BaseCog(mock_bot_with_container)

            # Verify bot is set
            assert cog.bot == mock_bot_with_container

            # Verify container is available but injection failed
            assert cog._container == mock_bot_with_container.container

            # Verify services are None due to injection failure
            assert cog.db_service is None
            assert cog.bot_service is None
            assert cog.config_service is None

            # Verify fallback was initialized
            mock_db_controller.assert_called_once()

    def test_db_property_with_injected_service(self, mock_bot_with_container):
        """Test db property returns controller from injected service."""
        cog = BaseCog(mock_bot_with_container)

        # Access db property
        db_controller = cog.db

        # Verify it returns the controller from the injected service
        assert db_controller == cog.db_service.get_controller()

    def test_db_property_with_fallback(self, mock_bot_without_container):
        """Test db property returns fallback controller when no injection."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_db_controller.return_value = mock_controller_instance

            cog = BaseCog(mock_bot_without_container)

            # Access db property
            db_controller = cog.db

            # Verify it returns the fallback controller
            assert db_controller == mock_controller_instance

    def test_db_property_injection_failure_fallback(self, mock_bot_with_container):
        """Test db property falls back when injected service fails."""
        cog = BaseCog(mock_bot_with_container)

        # Make injected service fail by replacing the method
        cog.db_service.get_controller = Mock(side_effect=Exception("Service failed"))

        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_db_controller.return_value = mock_controller_instance

            # Access db property
            db_controller = cog.db

            # Verify it falls back to direct instantiation
            assert db_controller == mock_controller_instance

    def test_db_property_no_controller_available(self, mock_bot_without_container):
        """Test db property raises error when no controller is available."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_db_controller.side_effect = Exception("Controller creation failed")

            cog = BaseCog(mock_bot_without_container)

            # Accessing db property should raise RuntimeError
            with pytest.raises(RuntimeError, match="No database controller available"):
                _ = cog.db

    def test_get_config_with_injected_service(self, mock_bot_with_container):
        """Test get_config uses injected config service."""
        cog = BaseCog(mock_bot_with_container)

        # Get config value
        value = cog.get_config("test_key", "default")

        # Verify it uses the injected service
        assert value == "test_value"

    def test_get_config_with_fallback(self, mock_bot_without_container):
        """Test get_config falls back to direct Config access."""
        with patch('tux.core.base_cog.Config') as mock_config_class:
            mock_config_instance = Mock()
            mock_config_instance.test_key = "fallback_value"
            mock_config_class.return_value = mock_config_instance

            cog = BaseCog(mock_bot_without_container)

            # Get config value
            value = cog.get_config("test_key", "default")

            # Verify it uses the fallback
            assert value == "fallback_value"

    def test_get_config_key_not_found(self, mock_bot_with_container):
        """Test get_config returns default when key not found."""
        cog = BaseCog(mock_bot_with_container)

        # Get non-existent config value
        value = cog.get_config("nonexistent_key", "default_value")

        # Verify it returns the default
        assert value == "default_value"

    def test_get_bot_latency_with_injected_service(self, mock_bot_with_container):
        """Test get_bot_latency uses injected bot service."""
        cog = BaseCog(mock_bot_with_container)

        # Get latency
        latency = cog.get_bot_latency()

        # Verify it uses the injected service
        assert latency == 0.123

    def test_get_bot_latency_with_fallback(self, mock_bot_without_container):
        """Test get_bot_latency falls back to direct bot access."""
        cog = BaseCog(mock_bot_without_container)

        # Get latency
        latency = cog.get_bot_latency()

        # Verify it uses the fallback
        assert latency == 0.456

    def test_get_bot_user_with_injected_service(self, mock_bot_with_container):
        """Test get_bot_user uses injected bot service."""
        cog = BaseCog(mock_bot_with_container)

        # Mock user in service
        mock_user = Mock(spec=discord.User)
        cog.bot_service._users[12345] = mock_user

        # Get user
        user = cog.get_bot_user(12345)

        # Verify it uses the injected service
        assert user == mock_user

    def test_get_bot_user_with_fallback(self, mock_bot_without_container):
        """Test get_bot_user falls back to direct bot access."""
        mock_user = Mock(spec=discord.User)
        mock_bot_without_container.get_user.return_value = mock_user

        cog = BaseCog(mock_bot_without_container)

        # Get user
        user = cog.get_bot_user(12345)

        # Verify it uses the fallback
        assert user == mock_user
        mock_bot_without_container.get_user.assert_called_once_with(12345)

    def test_get_bot_emoji_with_injected_service(self, mock_bot_with_container):
        """Test get_bot_emoji uses injected bot service."""
        cog = BaseCog(mock_bot_with_container)

        # Mock emoji in service
        mock_emoji = Mock(spec=discord.Emoji)
        cog.bot_service._emojis[67890] = mock_emoji

        # Get emoji
        emoji = cog.get_bot_emoji(67890)

        # Verify it uses the injected service
        assert emoji == mock_emoji

    def test_get_bot_emoji_with_fallback(self, mock_bot_without_container):
        """Test get_bot_emoji falls back to direct bot access."""
        mock_emoji = Mock(spec=discord.Emoji)
        mock_bot_without_container.get_emoji.return_value = mock_emoji

        cog = BaseCog(mock_bot_without_container)

        # Get emoji
        emoji = cog.get_bot_emoji(67890)

        # Verify it uses the fallback
        assert emoji == mock_emoji
        mock_bot_without_container.get_emoji.assert_called_once_with(67890)

    @pytest.mark.asyncio
    async def test_execute_database_query_with_injected_service(self, mock_bot_with_container):
        """Test execute_database_query uses injected database service."""
        cog = BaseCog(mock_bot_with_container)

        # Execute query
        result = await cog.execute_database_query("test_operation", "arg1", kwarg1="value1")

        # Verify it uses the injected service
        assert result == "mock_result_test_operation"

    @pytest.mark.asyncio
    async def test_execute_database_query_with_fallback(self, mock_bot_without_container):
        """Test execute_database_query falls back to direct controller access."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_method = AsyncMock(return_value="fallback_result")
            mock_controller_instance.test_operation = mock_method
            mock_db_controller.return_value = mock_controller_instance

            cog = BaseCog(mock_bot_without_container)

            # Execute query
            result = await cog.execute_database_query("test_operation", "arg1", kwarg1="value1")

            # Verify it uses the fallback
            assert result == "fallback_result"
            mock_method.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_execute_database_query_operation_not_found(self, mock_bot_without_container):
        """Test execute_database_query raises error for non-existent operation."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_db_controller.return_value = mock_controller_instance

            cog = BaseCog(mock_bot_without_container)

            # Execute non-existent operation
            with pytest.raises(AttributeError, match="DatabaseController has no operation 'nonexistent'"):
                await cog.execute_database_query("nonexistent")

    def test_repr(self, mock_bot_with_container, mock_bot_without_container):
        """Test string representation of BaseCog."""
        # Test with injection
        mock_bot_with_container.user = Mock()
        mock_bot_with_container.user.__str__ = Mock(return_value="TestBot#1234")
        cog_with_injection = BaseCog(mock_bot_with_container)
        repr_str = repr(cog_with_injection)
        assert "BaseCog" in repr_str
        assert "injection=injected" in repr_str

        # Test with fallback
        with patch('tux.core.base_cog.DatabaseController'):
            mock_bot_without_container.user = Mock()
            mock_bot_without_container.user.__str__ = Mock(return_value="TestBot#1234")
            cog_with_fallback = BaseCog(mock_bot_without_container)
            repr_str = repr(cog_with_fallback)
            assert "BaseCog" in repr_str
            assert "injection=fallback" in repr_str

    def test_service_injection_partial_failure(self, mock_bot_with_container):
        """Test BaseCog handles partial service injection failures gracefully."""
        # Make only database service injection fail
        def get_optional_side_effect(service_type):
            if service_type == IDatabaseService:
                raise Exception("Database service injection failed")
            elif service_type == IBotService:
                return MockBotService()
            elif service_type == IConfigService:
                return MockConfigService()
            return None

        mock_bot_with_container.container.get_optional.side_effect = get_optional_side_effect

        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_db_controller.return_value = Mock(spec=DatabaseController)

            cog = BaseCog(mock_bot_with_container)

            # Verify partial injection
            assert cog.db_service is None  # Failed injection
            assert cog.bot_service is not None  # Successful injection
            assert cog.config_service is not None  # Successful injection

            # Verify fallback database controller was created
            mock_db_controller.assert_called_once()

    def test_inheritance_from_commands_cog(self, mock_bot_with_container):
        """Test that BaseCog properly inherits from commands.Cog."""
        cog = BaseCog(mock_bot_with_container)

        # Verify inheritance
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'qualified_name')
        assert hasattr(cog, 'description')
