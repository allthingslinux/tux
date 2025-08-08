"""Unit tests for service interfaces."""

from typing import Any

import discord
import pytest

from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.services.database.controllers import DatabaseController


class MockDatabaseService:
    """Mock implementation of IDatabaseService for testing."""

    def __init__(self) -> None:
        self.controller = DatabaseController()

    def get_controller(self) -> DatabaseController:
        """Get the database controller instance."""
        return self.controller

    async def execute_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a database query operation."""
        return f"executed_{operation}"


class MockBotService:
    """Mock implementation of IBotService for testing."""

    def __init__(self) -> None:
        self._latency = 0.1
        self._user = None
        self._guilds: list[discord.Guild] = []

    @property
    def latency(self) -> float:
        """Get the bot's current latency to Discord."""
        return self._latency

    def get_user(self, user_id: int) -> discord.User | None:
        """Get a user by their ID."""
        return None  # Mock implementation

    def get_emoji(self, emoji_id: int) -> discord.Emoji | None:
        """Get an emoji by its ID."""
        return None  # Mock implementation

    @property
    def user(self) -> discord.ClientUser | None:
        """Get the bot's user object."""
        return self._user

    @property
    def guilds(self) -> list[discord.Guild]:
        """Get all guilds the bot is in."""
        return self._guilds


class MockConfigService:
    """Mock implementation of IConfigService for testing."""

    def __init__(self) -> None:
        self._config = {
            "database_url": "sqlite:///test.db",
            "bot_token": "test_token",
            "dev_mode": True,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def get_database_url(self) -> str:
        """Get the database URL for the current environment."""
        return self._config["database_url"]

    def get_bot_token(self) -> str:
        """Get the bot token for the current environment."""
        return self._config["bot_token"]

    def is_dev_mode(self) -> bool:
        """Check if the bot is running in development mode."""
        return self._config["dev_mode"]


class TestServiceInterfaces:
    """Test cases for service interface compliance."""

    def test_database_service_interface_compliance(self) -> None:
        """Test that MockDatabaseService implements IDatabaseService protocol."""
        service: IDatabaseService = MockDatabaseService()

        # Test get_controller method
        controller = service.get_controller()
        assert isinstance(controller, DatabaseController)

    @pytest.mark.asyncio
    async def test_database_service_execute_query(self) -> None:
        """Test database service execute_query method."""
        service: IDatabaseService = MockDatabaseService()

        result = await service.execute_query("test_operation", arg1="value1")
        assert result == "executed_test_operation"

    def test_bot_service_interface_compliance(self) -> None:
        """Test that MockBotService implements IBotService protocol."""
        service: IBotService = MockBotService()

        # Test latency property
        assert isinstance(service.latency, float)
        assert service.latency == 0.1

        # Test get_user method
        user = service.get_user(12345)
        assert user is None  # Mock returns None

        # Test get_emoji method
        emoji = service.get_emoji(67890)
        assert emoji is None  # Mock returns None

        # Test user property
        assert service.user is None  # Mock returns None

        # Test guilds property
        assert isinstance(service.guilds, list)
        assert len(service.guilds) == 0  # Mock returns empty list

    def test_config_service_interface_compliance(self) -> None:
        """Test that MockConfigService implements IConfigService protocol."""
        service: IConfigService = MockConfigService()

        # Test get method
        assert service.get("database_url") == "sqlite:///test.db"
        assert service.get("nonexistent", "default") == "default"

        # Test get_database_url method
        assert service.get_database_url() == "sqlite:///test.db"

        # Test get_bot_token method
        assert service.get_bot_token() == "test_token"

        # Test is_dev_mode method
        assert service.is_dev_mode() is True

    def test_protocol_structural_typing(self) -> None:
        """Test that protocols work with structural typing."""
        # This test verifies that any class with the right methods
        # can be used as the protocol type

        class AnotherDatabaseService:
            def get_controller(self) -> DatabaseController:
                return DatabaseController()

            async def execute_query(self, operation: str, *args: Any, **kwargs: Any) -> Any:
                return "another_result"

        # This should work due to structural typing
        service: IDatabaseService = AnotherDatabaseService()
        controller = service.get_controller()
        assert isinstance(controller, DatabaseController)
