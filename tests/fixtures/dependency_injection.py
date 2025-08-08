"""Testing utilities and fixtures for dependency injection system.

This module provides mock services, test fixtures, and helper functions
for testing the dependency injection system and cogs that use it.
"""

import time
from typing import Any
from unittest.mock import AsyncMock, Mock

import discord
import pytest
from discord.ext import commands

from tux.core.container import ServiceContainer
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.services.database.controllers import DatabaseController


class MockDatabaseService:
    """Mock implementation of IDatabaseService for testing.

    Provides a controllable mock database service that can be configured
    to return specific values or raise exceptions for testing scenarios.
    """

    def __init__(self) -> None:
        """Initialize the mock database service."""
        self._controller = Mock(spec=DatabaseController)
        self._query_results: dict[str, Any] = {}
        self._query_exceptions: dict[str, Exception] = {}
        self.call_count = 0

    def get_controller(self) -> DatabaseController:
        """Get the mock database controller.

        Returns:
            Mock database controller instance
        """
        self.call_count += 1
        return self._controller

    async def execute_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a mock database query operation.

        Args:
            operation: The operation name to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The configured result for the operation

        Raises:
            Exception: If an exception is configured for the operation
        """
        self.call_count += 1

        # Check if we should raise an exception
        if operation in self._query_exceptions:
            raise self._query_exceptions[operation]

        # Return configured result or default
        return self._query_results.get(operation, f"mock_result_for_{operation}")

    def set_query_result(self, operation: str, result: Any) -> None:
        """Configure the result for a specific query operation.

        Args:
            operation: The operation name
            result: The result to return for this operation
        """
        self._query_results[operation] = result

    def set_query_exception(self, operation: str, exception: Exception) -> None:
        """Configure an exception to raise for a specific query operation.

        Args:
            operation: The operation name
            exception: The exception to raise for this operation
        """
        self._query_exceptions[operation] = exception

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self._query_results.clear()
        self._query_exceptions.clear()
        self.call_count = 0
        self._controller.reset_mock()


class MockBotService:
    """Mock implementation of IBotService for testing.

    Provides a controllable mock bot service that can simulate
    various bot states and behaviors for testing.
    """

    def __init__(self) -> None:
        """Initialize the mock bot service."""
        self._latency = 0.1
        self._users: dict[int, discord.User] = {}
        self._emojis: dict[int, discord.Emoji] = {}
        self._user = Mock(spec=discord.ClientUser)
        self._guilds: list[discord.Guild] = []
        self.call_count = 0

    @property
    def latency(self) -> float:
        """Get the mock bot's latency.

        Returns:
            The configured latency value
        """
        self.call_count += 1
        return self._latency

    def get_user(self, user_id: int) -> discord.User | None:
        """Get a mock user by ID.

        Args:
            user_id: The Discord user ID

        Returns:
            The configured user object or None
        """
        self.call_count += 1
        return self._users.get(user_id)

    def get_emoji(self, emoji_id: int) -> discord.Emoji | None:
        """Get a mock emoji by ID.

        Args:
            emoji_id: The Discord emoji ID

        Returns:
            The configured emoji object or None
        """
        self.call_count += 1
        return self._emojis.get(emoji_id)

    @property
    def user(self) -> discord.ClientUser | None:
        """Get the mock bot's user object.

        Returns:
            The configured bot user object
        """
        self.call_count += 1
        return self._user

    @property
    def guilds(self) -> list[discord.Guild]:
        """Get the mock bot's guilds.

        Returns:
            List of configured guild objects
        """
        self.call_count += 1
        return self._guilds.copy()

    def set_latency(self, latency: float) -> None:
        """Set the mock bot's latency.

        Args:
            latency: The latency value to return
        """
        self._latency = latency

    def add_user(self, user_id: int, user: discord.User) -> None:
        """Add a user to the mock bot's user cache.

        Args:
            user_id: The user ID
            user: The user object
        """
        self._users[user_id] = user

    def add_emoji(self, emoji_id: int, emoji: discord.Emoji) -> None:
        """Add an emoji to the mock bot's emoji cache.

        Args:
            emoji_id: The emoji ID
            emoji: The emoji object
        """
        self._emojis[emoji_id] = emoji

    def set_user(self, user: discord.ClientUser) -> None:
        """Set the mock bot's user object.

        Args:
            user: The bot user object
        """
        self._user = user

    def add_guild(self, guild: discord.Guild) -> None:
        """Add a guild to the mock bot's guild list.

        Args:
            guild: The guild object
        """
        self._guilds.append(guild)

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self._latency = 0.1
        self._users.clear()
        self._emojis.clear()
        self._user = Mock(spec=discord.ClientUser)
        self._guilds.clear()
        self.call_count = 0


class MockConfigService:
    """Mock implementation of IConfigService for testing.

    Provides a controllable mock config service that can return
    configured values for testing different configuration scenarios.
    """

    def __init__(self) -> None:
        """Initialize the mock config service."""
        self._config_values: dict[str, Any] = {
            "DATABASE_URL": "sqlite:///test.db",
            "BOT_TOKEN": "test_token_123",
            "dev_mode": False,
        }
        self.call_count = 0

    def get(self, key: str, default: Any = None) -> Any:
        """Get a mock configuration value.

        Args:
            key: The configuration key
            default: Default value if key not found

        Returns:
            The configured value or default
        """
        self.call_count += 1
        return self._config_values.get(key, default)

    def get_database_url(self) -> str:
        """Get the mock database URL.

        Returns:
            The configured database URL
        """
        self.call_count += 1
        return self._config_values["DATABASE_URL"]

    def get_bot_token(self) -> str:
        """Get the mock bot token.

        Returns:
            The configured bot token
        """
        self.call_count += 1
        return self._config_values["BOT_TOKEN"]

    def is_dev_mode(self) -> bool:
        """Check if mock is in dev mode.

        Returns:
            The configured dev mode status
        """
        self.call_count += 1
        return self._config_values["dev_mode"]

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value for testing.

        Args:
            key: The configuration key
            value: The value to set
        """
        self._config_values[key] = value

    def set_database_url(self, url: str) -> None:
        """Set the mock database URL.

        Args:
            url: The database URL
        """
        self._config_values["DATABASE_URL"] = url

    def set_bot_token(self, token: str) -> None:
        """Set the mock bot token.

        Args:
            token: The bot token
        """
        self._config_values["BOT_TOKEN"] = token

    def set_dev_mode(self, dev_mode: bool) -> None:
        """Set the mock dev mode status.

        Args:
            dev_mode: Whether dev mode is enabled
        """
        self._config_values["dev_mode"] = dev_mode

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self._config_values = {
            "DATABASE_URL": "sqlite:///test.db",
            "BOT_TOKEN": "test_token_123",
            "dev_mode": False,
        }
        self.call_count = 0


# Performance testing utilities
class PerformanceTimer:
    """Utility for measuring service resolution performance."""

    def __init__(self) -> None:
        """Initialize the performance timer."""
        self.measurements: list[float] = []

    def __enter__(self) -> "PerformanceTimer":
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and record measurement."""
        end_time = time.perf_counter()
        self.measurements.append(end_time - self.start_time)

    @property
    def average_time(self) -> float:
        """Get the average measurement time."""
        return sum(self.measurements) / len(self.measurements) if self.measurements else 0.0

    @property
    def total_time(self) -> float:
        """Get the total measurement time."""
        return sum(self.measurements)

    @property
    def min_time(self) -> float:
        """Get the minimum measurement time."""
        return min(self.measurements) if self.measurements else 0.0

    @property
    def max_time(self) -> float:
        """Get the maximum measurement time."""
        return max(self.measurements) if self.measurements else 0.0

    def reset(self) -> None:
        """Reset all measurements."""
        self.measurements.clear()


# Pytest fixtures
@pytest.fixture
def mock_database_service() -> MockDatabaseService:
    """Provide a mock database service for testing.

    Returns:
        A fresh MockDatabaseService instance
    """
    return MockDatabaseService()


@pytest.fixture
def mock_bot_service() -> MockBotService:
    """Provide a mock bot service for testing.

    Returns:
        A fresh MockBotService instance
    """
    return MockBotService()


@pytest.fixture
def mock_config_service() -> MockConfigService:
    """Provide a mock config service for testing.

    Returns:
        A fresh MockConfigService instance
    """
    return MockConfigService()


@pytest.fixture
def mock_container(
    mock_database_service: MockDatabaseService,
    mock_bot_service: MockBotService,
    mock_config_service: MockConfigService,
) -> ServiceContainer:
    """Provide a service container with mock services registered.

    Args:
        mock_database_service: Mock database service
        mock_bot_service: Mock bot service
        mock_config_service: Mock config service

    Returns:
        A ServiceContainer with all mock services registered
    """
    container = ServiceContainer()
    container.register_instance(IDatabaseService, mock_database_service)
    container.register_instance(IBotService, mock_bot_service)
    container.register_instance(IConfigService, mock_config_service)
    return container


@pytest.fixture
def mock_bot() -> Mock:
    """Provide a mock Discord bot for testing.

    Returns:
        A mock bot instance with common attributes
    """
    bot = Mock(spec=commands.Bot)
    bot.latency = 0.1
    bot.user = Mock(spec=discord.ClientUser)
    bot.guilds = []
    bot.get_user = Mock(return_value=None)
    bot.get_emoji = Mock(return_value=None)
    return bot


@pytest.fixture
def mock_bot_with_container(mock_bot: Mock, mock_container: ServiceContainer) -> Mock:
    """Provide a mock bot with a dependency injection container.

    Args:
        mock_bot: Mock bot instance
        mock_container: Mock service container

    Returns:
        A mock bot with the container attached and all required attributes
    """
    # Attach the container
    mock_bot.container = mock_container

    # Ensure required attributes exist
    if not hasattr(mock_bot, 'user'):
        mock_bot.user = Mock()

    # Add any other required bot attributes here
    if not hasattr(mock_bot, 'guilds'):
        mock_bot.guilds = []

    # Add any required methods
    if not hasattr(mock_bot, 'get_user'):
        mock_bot.get_user = Mock(return_value=None)

    if not hasattr(mock_bot, 'get_emoji'):
        mock_bot.get_emoji = Mock(return_value=None)

    # Add any other required mocks here

    return mock_bot


@pytest.fixture
def performance_timer() -> PerformanceTimer:
    """Provide a performance timer for measuring execution times.

    Returns:
        A fresh PerformanceTimer instance
    """
    return PerformanceTimer()


# Helper functions for creating test containers
def create_test_container_with_mocks() -> tuple[ServiceContainer, MockDatabaseService, MockBotService, MockConfigService]:
    """Create a test container with mock services.

    Returns:
        A tuple containing the container and all mock services
    """
    container = ServiceContainer()

    mock_db = MockDatabaseService()
    mock_bot = MockBotService()
    mock_config = MockConfigService()

    container.register_instance(IDatabaseService, mock_db)
    container.register_instance(IBotService, mock_bot)
    container.register_instance(IConfigService, mock_config)

    return container, mock_db, mock_bot, mock_config


def create_test_container_with_real_services(bot: commands.Bot) -> ServiceContainer:
    """Create a test container with real service implementations.

    Args:
        bot: The Discord bot instance

    Returns:
        A ServiceContainer with real services registered
    """
    from tux.core.service_registry import ServiceRegistry
    return ServiceRegistry.configure_container(bot)


def measure_service_resolution_performance(
    container: ServiceContainer,
    service_type: type,
    iterations: int = 1000,
) -> dict[str, float]:
    """Measure the performance of service resolution.

    Args:
        container: The service container to test
        service_type: The service type to resolve
        iterations: Number of iterations to perform

    Returns:
        Dictionary with performance metrics
    """
    timer = PerformanceTimer()

    for _ in range(iterations):
        with timer:
            container.get(service_type)

    return {
        "total_time": timer.total_time,
        "average_time": timer.average_time,
        "min_time": timer.min_time,
        "max_time": timer.max_time,
        "iterations": iterations,
    }


def assert_service_resolution_performance(
    container: ServiceContainer,
    service_type: type,
    max_average_time: float = 0.001,  # 1ms
    iterations: int = 100,
) -> None:
    """Assert that service resolution meets performance requirements.

    Args:
        container: The service container to test
        service_type: The service type to resolve
        max_average_time: Maximum allowed average resolution time
        iterations: Number of iterations to perform

    Raises:
        AssertionError: If performance requirements are not met
    """
    metrics = measure_service_resolution_performance(container, service_type, iterations)

    assert metrics["average_time"] <= max_average_time, (
        f"Service resolution too slow: {metrics['average_time']:.6f}s > {max_average_time:.6f}s"
    )
