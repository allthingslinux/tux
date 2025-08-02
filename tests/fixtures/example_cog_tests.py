"""Example unit tests demonstrating how to test cogs with dependency injection.

This module provides examples of how to write unit tests for cogs that use
the dependency injection system, including both injection and fallback scenarios.
"""

import pytest
from discord.ext import commands
from unittest.mock import Mock, AsyncMock

from tux.core.base_cog import BaseCog
from tux.core.interfaces import IDatabaseService, IBotService, IConfigService
from tests.fixtures.dependency_injection import (
    MockDatabaseService,
    MockBotService,
    MockConfigService,
    create_test_container_with_mocks,
)


class ExampleCog(BaseCog):
    """Example cog for demonstrating dependency injection testing."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the example cog."""
        super().__init__(bot)

    @commands.command(name="example")
    async def example_command(self, ctx: commands.Context) -> None:
        """Example command that uses injected services."""
        # Use database service
        controller = self.db_service.get_controller()
        result = await self.db_service.execute_query("get_user_data", ctx.author.id)

        # Use bot service
        latency = self.bot_service.latency
        user = self.bot_service.get_user(ctx.author.id)

        # Use config service
        dev_mode = self.config_service.is_dev_mode()

        await ctx.send(f"Command executed! Latency: {latency}, Dev mode: {dev_mode}")

    async def get_user_level(self, user_id: int) -> int:
        """Example method that uses database service."""
        result = await self.db_service.execute_query("get_user_level", user_id)
        return result.get("level", 0) if isinstance(result, dict) else 0


class TestExampleCogWithDependencyInjection:
    """Test the ExampleCog with dependency injection."""

    @pytest.fixture
    def mock_ctx(self) -> Mock:
        """Create a mock command context."""
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock()
        ctx.author.id = 12345
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def cog_with_injection(self, mock_bot_with_container) -> ExampleCog:
        """Create an ExampleCog with dependency injection."""
        return ExampleCog(mock_bot_with_container)

    @pytest.fixture
    def cog_without_injection(self, mock_bot) -> ExampleCog:
        """Create an ExampleCog without dependency injection (fallback mode)."""
        # Remove container to test fallback
        if hasattr(mock_bot, 'container'):
            delattr(mock_bot, 'container')
        return ExampleCog(mock_bot)

    async def test_example_command_with_injection(
        self,
        cog_with_injection: ExampleCog,
        mock_ctx: Mock,
        mock_database_service: MockDatabaseService,
        mock_bot_service: MockBotService,
        mock_config_service: MockConfigService,
    ) -> None:
        """Test the example command with dependency injection."""
        # Configure mock services
        mock_database_service.set_query_result("get_user_data", {"user_id": 12345, "name": "TestUser"})
        mock_bot_service.set_latency(0.05)
        mock_config_service.set_dev_mode(True)

        # Execute the command
        await cog_with_injection.example_command(mock_ctx)

        # Verify service interactions
        assert mock_database_service.call_count >= 1
        assert mock_bot_service.call_count >= 1
        assert mock_config_service.call_count >= 1

        # Verify the response
        mock_ctx.send.assert_called_once()
        call_args = mock_ctx.send.call_args[0][0]
        assert "Latency: 0.05" in call_args
        assert "Dev mode: True" in call_args

    async def test_get_user_level_with_injection(
        self,
        cog_with_injection: ExampleCog,
        mock_database_service: MockDatabaseService,
    ) -> None:
        """Test the get_user_level method with dependency injection."""
        # Configure mock database service
        expected_result = {"level": 42}
        mock_database_service.set_query_result("get_user_level", expected_result)

        # Execute the method
        result = await cog_with_injection.get_user_level(12345)

        # Verify the result
        assert result == 42
        assert mock_database_service.call_count >= 1

    async def test_get_user_level_with_non_dict_result(
        self,
        cog_with_injection: ExampleCog,
        mock_database_service: MockDatabaseService,
    ) -> None:
        """Test get_user_level when database returns non-dict result."""
        # Configure mock to return non-dict result
        mock_database_service.set_query_result("get_user_level", "invalid_result")

        # Execute the method
        result = await cog_with_injection.get_user_level(12345)

        # Should return default value
        assert result == 0

    async def test_database_service_error_handling(
        self,
        cog_with_injection: ExampleCog,
        mock_database_service: MockDatabaseService,
    ) -> None:
        """Test error handling when database service fails."""
        # Configure mock to raise exception
        mock_database_service.set_query_exception("get_user_level", RuntimeError("Database error"))

        # Execute the method and expect exception
        with pytest.raises(RuntimeError, match="Database error"):
            await cog_with_injection.get_user_level(12345)

    def test_cog_initialization_with_injection(self, mock_bot_with_container) -> None:
        """Test that cog initializes correctly with dependency injection."""
        cog = ExampleCog(mock_bot_with_container)

        # Verify services are injected
        assert cog.db_service is not None
        assert cog.bot_service is not None
        assert cog.config_service is not None
        assert isinstance(cog.db_service, MockDatabaseService)
        assert isinstance(cog.bot_service, MockBotService)
        assert isinstance(cog.config_service, MockConfigService)

    def test_cog_initialization_without_injection(self, mock_bot) -> None:
        """Test that cog initializes correctly without dependency injection (fallback)."""
        # Ensure no container is present
        if hasattr(mock_bot, 'container'):
            delattr(mock_bot, 'container')

        cog = ExampleCog(mock_bot)

        # Verify fallback services are created
        assert cog.db_service is not None
        assert cog.bot_service is not None
        assert cog.config_service is not None
        # In fallback mode, these would be real service instances
        # The exact type depends on the BaseCog implementation

    async def test_service_performance_with_injection(
        self,
        cog_with_injection: ExampleCog,
        mock_database_service: MockDatabaseService,
    ) -> None:
        """Test that service resolution performance is acceptable."""
        # Configure mock service
        mock_database_service.set_query_result("get_user_level", {"level": 1})

        # Measure performance of multiple calls
        import time
        start_time = time.perf_counter()

        for _ in range(100):
            await cog_with_injection.get_user_level(12345)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Should complete 100 calls in reasonable time (less than 1 second)
        assert total_time < 1.0, f"Service calls too slow: {total_time:.3f}s for 100 calls"

    def test_service_call_counting(
        self,
        cog_with_injection: ExampleCog,
        mock_database_service: MockDatabaseService,
        mock_bot_service: MockBotService,
        mock_config_service: MockConfigService,
    ) -> None:
        """Test that we can track service call counts for verification."""
        # Reset call counts
        mock_database_service.reset()
        mock_bot_service.reset()
        mock_config_service.reset()

        # Access services
        _ = cog_with_injection.db_service.get_controller()
        _ = cog_with_injection.bot_service.latency
        _ = cog_with_injection.config_service.is_dev_mode()

        # Verify call counts
        assert mock_database_service.call_count == 1
        assert mock_bot_service.call_count == 1
        assert mock_config_service.call_count == 1


class TestServiceMockingPatterns:
    """Demonstrate different patterns for mocking services."""

    def test_mock_database_service_configuration(self) -> None:
        """Test different ways to configure mock database service."""
        mock_db = MockDatabaseService()

        # Test setting query results
        mock_db.set_query_result("get_user", {"id": 123, "name": "Test"})
        mock_db.set_query_result("get_guild", {"id": 456, "name": "TestGuild"})

        # Test setting exceptions
        mock_db.set_query_exception("delete_user", RuntimeError("Permission denied"))

        # Verify configuration works
        assert mock_db._query_results["get_user"] == {"id": 123, "name": "Test"}
        assert mock_db._query_results["get_guild"] == {"id": 456, "name": "TestGuild"}
        assert isinstance(mock_db._query_exceptions["delete_user"], RuntimeError)

    def test_mock_bot_service_configuration(self) -> None:
        """Test different ways to configure mock bot service."""
        mock_bot = MockBotService()

        # Test setting properties
        mock_bot.set_latency(0.123)

        # Test adding users and emojis
        user_mock = Mock()
        emoji_mock = Mock()
        mock_bot.add_user(12345, user_mock)
        mock_bot.add_emoji(67890, emoji_mock)

        # Verify configuration
        assert mock_bot.latency == 0.123
        assert mock_bot.get_user(12345) == user_mock
        assert mock_bot.get_emoji(67890) == emoji_mock
        assert mock_bot.get_user(99999) is None  # Not configured

    def test_mock_config_service_configuration(self) -> None:
        """Test different ways to configure mock config service."""
        mock_config = MockConfigService()

        # Test setting configuration values
        mock_config.set_config_value("custom_setting", "test_value")
        mock_config.set_database_url("postgresql://test:test@localhost/test")
        mock_config.set_dev_mode(True)

        # Verify configuration
        assert mock_config.get("custom_setting") == "test_value"
        assert mock_config.get_database_url() == "postgresql://test:test@localhost/test"
        assert mock_config.is_dev_mode() is True

    def test_container_with_mixed_services(self) -> None:
        """Test creating containers with mix of mock and real services."""
        container, mock_db, mock_bot, mock_config = create_test_container_with_mocks()

        # Verify all services are registered
        assert container.is_registered(IDatabaseService)
        assert container.is_registered(IBotService)
        assert container.is_registered(IConfigService)

        # Verify we get the mock instances
        db_service = container.get(IDatabaseService)
        bot_service = container.get(IBotService)
        config_service = container.get(IConfigService)

        assert db_service is mock_db
        assert bot_service is mock_bot
        assert config_service is mock_config


# Example of testing a more complex cog with multiple service interactions
class ComplexExampleCog(BaseCog):
    """More complex example cog for advanced testing scenarios."""

    async def process_user_action(self, user_id: int, action: str) -> dict:
        """Process a user action involving multiple services."""
        # Get user data from database
        user_data = await self.db_service.execute_query("get_user", user_id)

        # Check if user exists in bot cache
        discord_user = self.bot_service.get_user(user_id)

        # Get configuration for action processing
        action_config = self.config_service.get(f"action_{action}", {})

        # Process the action
        result = {
            "user_id": user_id,
            "action": action,
            "user_exists_in_db": user_data is not None,
            "user_exists_in_cache": discord_user is not None,
            "action_enabled": action_config.get("enabled", False),
            "processed_at": "2024-01-01T00:00:00Z",  # Mock timestamp
        }

        # Log the action if in dev mode
        if self.config_service.is_dev_mode():
            await self.db_service.execute_query("log_action", user_id, action, result)

        return result


class TestComplexExampleCog:
    """Test the more complex example cog."""

    @pytest.fixture
    def complex_cog(self, mock_bot_with_container) -> ComplexExampleCog:
        """Create a ComplexExampleCog with dependency injection."""
        return ComplexExampleCog(mock_bot_with_container)

    async def test_process_user_action_full_scenario(
        self,
        complex_cog: ComplexExampleCog,
        mock_database_service: MockDatabaseService,
        mock_bot_service: MockBotService,
        mock_config_service: MockConfigService,
    ) -> None:
        """Test the full user action processing scenario."""
        # Configure mocks
        user_data = {"id": 12345, "name": "TestUser"}
        discord_user = Mock()
        action_config = {"enabled": True, "max_uses": 10}

        mock_database_service.set_query_result("get_user", user_data)
        mock_bot_service.add_user(12345, discord_user)
        mock_config_service.set_config_value("action_test", action_config)
        mock_config_service.set_dev_mode(True)

        # Execute the method
        result = await complex_cog.process_user_action(12345, "test")

        # Verify the result
        assert result["user_id"] == 12345
        assert result["action"] == "test"
        assert result["user_exists_in_db"] is True
        assert result["user_exists_in_cache"] is True
        assert result["action_enabled"] is True

        # Verify service interactions
        assert mock_database_service.call_count >= 2  # get_user + log_action
        assert mock_bot_service.call_count >= 1  # get_user
        assert mock_config_service.call_count >= 2  # get action config + is_dev_mode

    async def test_process_user_action_user_not_found(
        self,
        complex_cog: ComplexExampleCog,
        mock_database_service: MockDatabaseService,
        mock_bot_service: MockBotService,
        mock_config_service: MockConfigService,
    ) -> None:
        """Test user action processing when user is not found."""
        # Configure mocks for user not found scenario
        mock_database_service.set_query_result("get_user", None)
        # Don't add user to bot service (will return None)
        mock_config_service.set_config_value("action_test", {"enabled": False})
        mock_config_service.set_dev_mode(False)

        # Execute the method
        result = await complex_cog.process_user_action(99999, "test")

        # Verify the result
        assert result["user_exists_in_db"] is False
        assert result["user_exists_in_cache"] is False
        assert result["action_enabled"] is False

        # Verify no logging occurred (dev mode is False)
        # The log_action should not have been called
        assert mock_database_service.call_count == 1  # Only get_user
