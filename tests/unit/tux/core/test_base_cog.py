"""Unit tests for the BaseCog class with dependency injection support."""

from __future__ import annotations

import logging
import types
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from _pytest.logging import LogCaptureFixture  # type: ignore[import-untyped]
from discord.ext import commands

# Set up logging
logger = logging.getLogger(__name__)

from tux.core.base_cog import BaseCog
from tux.core.container import ServiceContainer
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.services.database.controllers import DatabaseController

# Type variables for testing
BotT = TypeVar('BotT', bound=Union[commands.Bot, IBotService])
CogT = TypeVar('CogT', bound=BaseCog)

# Type aliases for test fixtures
MockBot = Union[commands.Bot, IBotService, Mock]
MockContainer = Union[ServiceContainer, Mock]


# Mock classes with proper type hints


class MockDatabaseService(IDatabaseService):
    """Mock implementation of IDatabaseService for testing."""

    def __init__(self) -> None:
        self._database_controller: DatabaseController = Mock(spec=DatabaseController)
        self._initialized: bool = False
        self._is_connected: bool = False
        self._latency: float = 0.0
        self._user: discord.ClientUser | None = None
        self._version: str = "1.0.0"

    @property
    def database_controller(self) -> DatabaseController:
        return self._database_controller

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def latency(self) -> float:
        return self._latency

    @property
    def user(self) -> discord.ClientUser | None:
        return self._user

    @property
    def version(self) -> str:
        return self._version

    async def initialize(self) -> None:
        self._initialized = True

    async def connect(self) -> None:
        self._is_connected = True

    async def disconnect(self) -> None:
        self._is_connected = False

    async def get_database_controller(self) -> DatabaseController:
        return self.database_controller

    def get_controller(self) -> DatabaseController:
        return self.database_controller

    def get_database_url(self) -> str:
        return "sqlite:///:memory:"

    def get_bot_token(self) -> str:
        return "mock_bot_token"

    def is_production(self) -> bool:
        return False

    def is_dev_mode(self) -> bool:
        return True

    async def execute_query(self, operation: str, *args: Any, **kwargs: Any) -> str:
        return f"Executed: {operation}"


class MockBotService(IBotService):
    """Mock implementation of IBotService for testing."""

    def __init__(self) -> None:
        """Initialize the mock bot service with test data."""
        self._user = Mock(spec=discord.ClientUser)
        self._user.id = 1234567890
        self._user.name = "TestBot"
        self._user.discriminator = "1234"
        self._user.avatar = None

        self._emojis: list[discord.Emoji] = []
        self._users: list[discord.User] = []
        self._guilds: list[discord.Guild] = []
        self._extensions: dict[str, types.ModuleType] = {}
        self._latency = 0.123
        self._cogs: dict[str, commands.Cog] = {}

    @property
    def user(self) -> discord.ClientUser:
        """Get the bot's user."""
        return self._user

    @property
    def emojis(self) -> list[discord.Emoji]:
        """Get a list of emojis the bot can use."""
        return self._emojis

    @property
    def users(self) -> list[discord.User]:
        """Get a list of users the bot can see."""
        return self._users

    @property
    def guilds(self) -> list[discord.Guild]:
        """Get a list of guilds the bot is in."""
        return self._guilds

    @property
    def cogs(self) -> dict[str, commands.Cog]:
        """Get the bot's cogs."""
        return self._cogs

    @property
    def extensions(self) -> dict[str, types.ModuleType]:
        """Get the bot's extensions."""
        return self._extensions

    def get_user(self, user_id: int) -> discord.User | None:
        """Get a user by ID."""
        return next((u for u in self._users if getattr(u, 'id', None) == user_id), None)

    def get_emoji(self, emoji_id: int) -> discord.Emoji | None:
        """Get an emoji by ID."""
        return next((e for e in self._emojis if getattr(e, 'id', None) == emoji_id), None)

    def get_cog(self, name: str) -> commands.Cog | None:
        """Get a cog by name."""
        return self._cogs.get(name)

    def load_extension(self, name: str) -> None:
        """Load an extension."""
        if name in self._extensions:
            raise commands.ExtensionAlreadyLoaded(name)
        self._extensions[name] = types.ModuleType(name)

    def unload_extension(self, name: str) -> None:
        """Unload an extension."""
        if name not in self._extensions:
            raise commands.ExtensionNotLoaded(name)
        del self._extensions[name]

    def reload_extension(self, name: str) -> None:
        """Reload an extension."""
        if name not in self._extensions:
            raise commands.ExtensionNotLoaded(name)
        self._extensions[name] = types.ModuleType(name)

    @property
    def latency(self) -> float:
        """Get the bot's latency."""
        return self._latency

    def is_production(self) -> bool:
        """Check if the bot is in production mode."""
        return False

    def is_dev_mode(self) -> bool:
        return True


class MockConfigService(IConfigService):
    """Mock implementation of IConfigService for testing."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {
            "token": "mock_bot_token",
            "prefix": "!",
            "database_url": "sqlite:///:memory:",
            "debug": True,
            "test_mode": True,
            "bot_name": "TestBot",
            "owner_id": 1234567890,
            "version": "1.0.0",
        }
        self._initialized: bool = False
        self._env: dict[str, str] = {}

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        value = self._config.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self._config.get(key, default))
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self._config.get(key, default))
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self._config.get(key, default)
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "y", "t")
        return bool(value)

    def get_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        if default is None:
            default = []
        value = self._config.get(key, default)
        return list(value) if isinstance(value, (list, tuple)) else default  # type: ignore[arg-type]

    def get_dict(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        if default is None:
            default = {}
        value = self._config.get(key, default)
        return dict(value) if isinstance(value, dict) else default  # type: ignore[arg-type]

    def get_env(self, key: str, default: str = "") -> str:
        return self._env.get(key, default)

    def set_env(self, key: str, value: str) -> None:
        self._env[key] = value

    def reload(self) -> None:
        pass  # No-op for mock

    def save(self) -> None:
        pass  # No-op for mock

    def get_database_url(self) -> str:
        return self._config.get("database_url", "sqlite:///:memory:")

    def get_bot_token(self) -> str:
        return self._config.get("token", "")

    def is_production(self) -> bool:
        return not self._config.get("debug", True)

    def is_dev_mode(self) -> bool:
        return self._config.get("debug", True)

class TestBaseCog:
    """Test cases for BaseCog class."""

    @pytest.fixture
    def mock_db_service(self) -> Mock:
        """Fixture that provides a mock database service."""
        from unittest.mock import AsyncMock
        mock_db = Mock(spec=IDatabaseService)
        mock_db.execute_query = AsyncMock(return_value=[{"id": 1, "name": "test"}])
        return mock_db

    @pytest.fixture
    def test_bot(self) -> Mock:
        """Fixture that provides a test bot instance."""
        bot = Mock(spec=commands.Bot)
        bot.user = Mock(spec=discord.ClientUser)
        bot.user.id = 1234567890
        bot.user.name = "TestBot"
        bot.container = Mock(spec=ServiceContainer)
        return bot

    @pytest.fixture
    def test_cog(self, test_bot: Mock) -> BaseCog:
        """Fixture that provides a test BaseCog instance."""
        return BaseCog(test_bot)

    def _create_mock_bot(self) -> Mock:
        """Helper method to create a mock bot with proper typing."""
        bot = Mock(spec=commands.Bot)
        bot.latency = 0.456
        bot.get_user = Mock(return_value=None)
        bot.get_emoji = Mock(return_value=None)
        bot.user = Mock(spec=discord.ClientUser)
        bot.user.id = 12345
        bot.user.name = "TestBot"
        # Initialize protected attributes
        setattr(bot, '_users', {})
        setattr(bot, '_emojis', {})
        setattr(bot, '_extensions', {})
        return bot

    @pytest.fixture
    def mock_bot(self) -> Mock:
        """Fixture that returns a mock bot instance with proper typing."""
        return self._create_mock_bot()

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Fixture that returns a mock service container with proper typing."""
        container = Mock(spec=ServiceContainer)
        container.get_optional = Mock(return_value=None)

        # Mock services for the container
        db_service = MockDatabaseService()
        bot_service = MockBotService()
        config_service = MockConfigService()

        def get_optional_side_effect(service_type: type[Any]) -> MockDatabaseService | MockBotService | MockConfigService | None:
            """Side effect function for container.get_optional.

            Args:
                service_type: The service type to get an instance for.

            Returns:
                An instance of the requested service type or None if not found.
            """
            if service_type == IDatabaseService:
                return db_service
            elif service_type == IBotService:
                return bot_service
            elif service_type == IConfigService:
                return config_service
            return None

        container.get_optional.side_effect = get_optional_side_effect
        return container
    def mock_bot_with_container(self, mock_bot: Mock, mock_container: Mock) -> Mock:
        """Fixture that returns a mock bot with a container attached."""
        # Use setattr to avoid mypy protected access error
        setattr(mock_bot, 'container', mock_container)
        return mock_bot

    @pytest.fixture
    def mock_bot_without_container(self) -> Mock:
        """Create a mock bot without dependency injection container."""
        bot = self._create_mock_bot()
        if hasattr(bot, 'container'):
            delattr(bot, 'container')
        return bot

    def test_init_with_container_successful_injection(self, mock_bot_with_container: Mock) -> None:
        """Test BaseCog initialization with successful service injection."""
        # Create a mock for the Tux bot with the required interface
        mock_tux_bot = Mock(spec=commands.Bot)

        # Set up the container attribute
        mock_tux_bot.container = mock_bot_with_container.container

        # Set up required attributes
        mock_tux_bot.user = Mock(spec=discord.ClientUser)
        mock_tux_bot.user.id = 12345
        mock_tux_bot.user.name = 'TestBot'
        mock_tux_bot.latency = 0.1
        mock_tux_bot.cogs = {}
        mock_tux_bot.extensions = {}

        # Set up required methods
        mock_tux_bot.get_user.return_value = None
        mock_tux_bot.get_emoji.return_value = None

        # Create the cog with the mock Tux bot
        cog = BaseCog(mock_tux_bot)  # type: ignore[arg-type]

        # Verify bot is set
        assert cog.bot == mock_tux_bot

        # Verify container is available through getter
        assert hasattr(cog, '_container')
        assert getattr(cog, '_container') == mock_bot_with_container.container

        # Verify services are injected
        assert cog.db_service is not None
        assert cog.bot_service is not None
        assert cog.config_service is not None

        # Verify container was called for each service
        assert mock_bot_with_container.container.get_optional.call_count >= 3

    def test_init_without_container_fallback(self, mock_bot_without_container: Mock) -> None:
        """Test BaseCog initialization without container falls back to default services."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_db_controller.return_value = mock_controller_instance

            # Type the mock bot to match expected interface
            bot: commands.Bot | IBotService = mock_bot_without_container

            # Create the cog with the properly typed mock bot
            cog = BaseCog(bot)  # type: ignore[arg-type]

            # Verify bot is set
            assert cog.bot == bot

            # Verify services are None (fallback mode)
            assert cog.db_service is None
            assert cog.bot_service is None
            assert cog.config_service is None

            # Verify no container is set
            assert not hasattr(cog, '_container')

            # Verify fallback database controller was created
            mock_db_controller.assert_called_once()

    def test_init_with_container_injection_failure(self, mock_bot_with_container: Mock) -> None:
        """Test BaseCog initialization handles service injection failures gracefully."""
        # Make container.get_optional raise an exception
        mock_bot_with_container.container.get_optional.side_effect = Exception("Injection failed")

        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_db_controller.return_value = Mock(spec=DatabaseController)

            cog = BaseCog(mock_bot_with_container)

            # Verify bot is set
            assert cog.bot == mock_bot_with_container

            # Verify container is available but injection failed
            # Using protected access in test to verify internal state
            assert cog._container == mock_bot_with_container.container  # type: ignore[attr-defined]

            # Verify services are None due to injection failure
            assert cog.db_service is None
            assert cog.bot_service is None
            assert cog.config_service is None

            # Verify fallback was initialized
            mock_db_controller.assert_called_once()

    def test_db_property_with_injected_service(self, mock_bot_with_container: Mock) -> None:
        """Test db property returns controller from injected service."""
        cog = BaseCog(mock_bot_with_container)

        # Access db property and verify it returns the controller from the injected service
        db_controller = cog.db
        assert cog.db_service is not None, "db_service should be available in this test"
        assert db_controller == cog.db_service.get_controller()

    def test_db_property_with_fallback(self, mock_bot_without_container: Mock) -> None:
        """Test db property returns fallback controller when no injection."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller_class:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_db_controller_class.return_value = mock_controller_instance

            cog = BaseCog(mock_bot_without_container)

            # Access db property
            db_controller = cog.db

            # Verify it returns a DatabaseController instance
            assert isinstance(db_controller, Mock)
            assert db_controller == mock_controller_instance

    def test_db_property_injection_failure_fallback(self, mock_bot_with_container: Mock) -> None:
        """Test db property falls back when injected service fails."""
        cog = BaseCog(mock_bot_with_container)

        # Make injected service fail by replacing the method
        if cog.db_service is not None:  # Check for None to satisfy type checker
            cog.db_service.get_controller = Mock(side_effect=Exception("Service failed"))

        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_db_controller.return_value = mock_controller_instance

            # Access db property
            db_controller = cog.db

            # Verify it falls back to direct instantiation
            assert db_controller == mock_controller_instance

    def test_db_property_no_controller_available(self, mock_bot_without_container: Mock) -> None:
        """Test db property raises error when no controller is available."""
        # Patch the DatabaseController to raise an exception when instantiated
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_db_controller.side_effect = Exception("Controller creation failed")

            # Also patch _init_fallback_services to prevent it from being called in __init__
            with patch.object(BaseCog, '_init_fallback_services'):
                cog = BaseCog(mock_bot_without_container)

                # Use protected access to force the fallback initialization
                # This is okay in tests as we need to test edge cases
                cog._db_controller = None  # type: ignore[assignment]

                # Accessing db property should raise RuntimeError
                with pytest.raises(RuntimeError, match="No database controller available"):
                    _ = cog.db

    def test_get_config_with_injected_service(self, mock_bot_with_container: Mock) -> None:
        """Test get_config uses injected config service."""
        # Get the config service from the container
        config_service = mock_bot_with_container.container.get_optional(IConfigService)
        # Create a mock for the get method
        mock_get = Mock(return_value="test_value")
        # Replace the get method with our mock
        config_service.get = mock_get

        cog = BaseCog(mock_bot_with_container)

        # Get config value
        value = cog.get_config("test_key", "default")

        # Verify it uses the injected service
        mock_get.assert_called_once_with("test_key", "default")
        assert value == "test_value"

    def test_get_config_with_fallback(self, mock_bot_without_container: Mock) -> None:
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

    def test_get_config_key_not_found(self, mock_bot_with_container: Mock) -> None:
        """Test get_config returns default when key not found."""
        cog = BaseCog(mock_bot_with_container)

        # Get non-existent config value
        value = cog.get_config("nonexistent_key", "default_value")

        # Verify it returns the default
        assert value == "default_value"

    def test_get_bot_latency_with_injected_service(self, mock_bot_with_container: Mock) -> None:
        """Test get_bot_latency uses injected bot service."""
        cog = BaseCog(mock_bot_with_container)

        # Get latency
        latency = cog.get_bot_latency()

        # Verify it uses the injected service
        assert latency == 0.123

    def test_get_bot_latency_with_fallback(self, mock_bot_without_container: Mock) -> None:
        """Test get_bot_latency falls back to direct bot access."""
        cog = BaseCog(mock_bot_without_container)

        # Get latency
        latency = cog.get_bot_latency()

        # Verify it uses the fallback
        assert latency == 0.456

    @pytest.mark.asyncio
    async def test_get_bot_user_with_injected_service(self, mock_bot_with_container: Mock) -> None:
        """Test get_bot_user uses injected bot service."""
        cog = BaseCog(mock_bot_with_container)

        # Mock user in service using the public API
        mock_user = Mock(spec=discord.User)
        mock_user.id = 12345
        # Ensure bot_service is properly typed and not None
        assert cog.bot_service is not None, "Bot service should be initialized"
        # Use the public API to get a user
        cog.bot_service.get_user = Mock(return_value=mock_user)  # type: ignore[method-assign]

        # Get user
        user = await cog.get_bot_user(12345)

        # Verify it uses the injected service
        assert user == mock_user

    def test_get_user_returns_user(self, mock_bot: Mock) -> None:
        """Test get_user returns a user when found in the cache."""
        # Setup test user
        user = Mock(spec=discord.User)
        user.id = 12345

        # Mock the get_user method to return our test user
        mock_bot.get_user.return_value = user

        # Test
        result = mock_bot.get_user(user.id)
        assert result == user
        mock_bot.get_user.assert_called_once_with(user.id)

    def test_get_bot_user_with_fallback(self, mock_bot_without_container: Mock) -> None:
        """Test get_bot_user falls back to direct bot access."""
        mock_user = Mock(spec=discord.User)
        mock_bot_without_container.get_user.return_value = mock_user

        cog = BaseCog(mock_bot_without_container)

        # Get user
        user = cog.get_bot_user(12345)

        # Verify it uses the fallback
        assert user == mock_user
        mock_bot_without_container.get_user.assert_called_once_with(12345)

    def test_get_bot_emoji_with_injected_service(
        self,
        mock_bot_with_container: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test get_bot_emoji uses injected bot service."""
        # Enable debug logging for this test
        caplog.set_level(logging.DEBUG)

        # Get the container from the fixture
        container = mock_bot_with_container.container
        logger.debug("[TEST] Container: %s", container)
        logger.debug("[TEST] Container type: %s", type(container).__name__)
        logger.debug("[TEST] Container dir: %s", dir(container))

        # Create a mock emoji with proper attributes
        mock_emoji = Mock(spec=discord.Emoji)
        mock_emoji.id = 67890

        # Create a mock bot service with our test emoji
        bot_service = MockBotService()
        # Access protected member to set up test data
        bot_service._emojis = [mock_emoji]  # type: ignore[attr-defined]
        logger.debug(
            "[TEST] Created bot service with emojis: %s",
            bot_service._emojis,  # type: ignore[attr-defined]
        )

        # Set up the container to return our mock services
        def get_optional_side_effect(service_type: type[Any]) -> Any:
            logger.debug(
                "[TEST] get_optional called with service_type: %s, is IBotService: %s",
                service_type,
                service_type == IBotService,
            )
            logger.debug(f"[TEST] service_type name: {getattr(service_type, '__name__', 'unknown')}")
            logger.debug(f"[TEST] service_type module: {getattr(service_type, '__module__', 'unknown')}")

            if service_type == IBotService:
                logger.debug(f"[TEST] Returning bot service: {bot_service}")
                return bot_service
            if service_type == IDatabaseService:
                logger.debug("[TEST] Returning mock database service")
                return MockDatabaseService()
            if service_type == IConfigService:
                logger.debug("[TEST] Returning mock config service")
                return MockConfigService()
            logger.debug(f"[TEST] No service found for type: {service_type}")
            return None

        # Configure the container to use our side effect
        container.get_optional.side_effect = get_optional_side_effect

        # Log the container's get_optional method before we modify it
        logger.debug(f"[TEST] Container get_optional before: {container.get_optional}")

        # Make sure the bot has the container attribute
        if not hasattr(mock_bot_with_container, 'container'):
            setattr(mock_bot_with_container, 'container', container)

        logger.debug(f"[TEST] Bot container before BaseCog init: {getattr(mock_bot_with_container, 'container', 'NOT SET')}")

        # Create the cog with the mock bot that has the container
        logger.debug("[TEST] Creating BaseCog instance")
        cog = BaseCog(mock_bot_with_container)

        # Debug log the cog's state
        logger.debug(f"[TEST] Cog state after initialization - has container: {hasattr(cog, '_container')}")
        logger.debug(f"[TEST] Cog _container: {getattr(cog, '_container', 'NOT SET')}")
        logger.debug(f"[TEST] Cog bot_service: {getattr(cog, 'bot_service', 'NOT SET')}")
        logger.debug(f"[TEST] Cog dir: {[attr for attr in dir(cog) if not attr.startswith('_')]}")

        # Debug log the test state
        logger.debug("[TEST] Test state after initialization:")
        logger.debug(
            "[TEST] - cog._container exists: %s, cog.bot_service: %s, type: %s",
            hasattr(cog, '_container'),
            getattr(cog, 'bot_service', 'NOT SET'),
            type(getattr(cog, 'bot_service', None)).__name__ if hasattr(cog, 'bot_service') else 'N/A',
        )

        # Verify the bot service was injected
        assert cog.bot_service is not None, "Bot service was not injected"
        logger.debug(f"[TEST] Bot service injected successfully: {cog.bot_service}")

        # Test getting the emoji
        logger.debug("[TEST] Testing get_bot_emoji")
        emoji = cog.get_bot_emoji(67890)
        assert emoji is not None
        assert emoji.id == 67890

        # Get the emoji (synchronous call)
        logger.debug("Calling get_bot_emoji")
        emoji = cog.get_bot_emoji(67890)

        # Verify it returns the correct emoji
        assert emoji is not None, "Emoji not found"
        assert emoji.id == 67890, f"Unexpected emoji ID: {getattr(emoji, 'id', None)}"

    def test_get_emoji_returns_emoji(self, mock_bot: Mock) -> None:
        """Test get_emoji returns an emoji when found in the cache."""
        # Setup test emoji
        emoji = Mock(spec=discord.Emoji)
        emoji.id = 54321

        # Mock the get_emoji method to return our test emoji
        mock_bot.get_emoji.return_value = emoji

        # Test
        result = mock_bot.get_emoji(emoji.id)
        assert result == emoji
        mock_bot.get_emoji.assert_called_once_with(emoji.id)

    def test_get_bot_emoji_with_fallback(self, mock_bot_without_container: Mock) -> None:
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
    async def test_execute_database_query_with_injected_service(
        self, mock_bot_with_container: Mock,
    ) -> None:
        """Test execute_database_query uses injected database service."""
        # Create a mock database service with an execute_query method
        mock_db_service = AsyncMock(spec=IDatabaseService)
        mock_db_service.execute_query.return_value = "mock_result_test_operation"

        # Get the container from the mock bot
        container = mock_bot_with_container.container
        assert container is not None, "Container should not be None"

        # Set up the container to return our mock database service
        def get_db_service_side_effect(service_type: type[Any]) -> IDatabaseService | None:
            return mock_db_service if service_type == IDatabaseService else None

        container.get_optional.side_effect = get_db_service_side_effect

        # Create the cog with our mocked container
        cog = BaseCog(mock_bot_with_container)

        # Execute query
        result = await cog.execute_database_query("test_operation", "arg1", kwarg1="value1")

        # Verify it uses the injected service
        mock_db_service.execute_query.assert_awaited_once_with("test_operation", "arg1", kwarg1="value1")
        assert result == "mock_result_test_operation"

    @pytest.mark.asyncio
    async def test_execute_database_query_with_fallback(self, mock_bot_without_container: Mock) -> None:
        """Test execute_database_query falls back to direct controller access."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            mock_controller_instance = Mock(spec=DatabaseController)
            mock_method = AsyncMock(return_value="fallback_result")
            mock_controller_instance.test_operation = mock_method
            mock_db_controller.return_value = mock_controller_instance

            cog = BaseCog(mock_bot_without_container)  # type: ignore[arg-type]

            # Execute query
            result = await cog.execute_database_query("test_operation", "arg1", kwarg1="value1")

            # Verify it uses the fallback
            mock_method.assert_awaited_once_with("arg1", kwarg1="value1")
            assert result == "fallback_result"
        with patch('tux.core.base_cog.DatabaseController'):
            mock_bot_without_container.user = Mock()
            mock_bot_without_container.user.__str__ = Mock(return_value="TestBot#1234")
            cog_with_fallback = BaseCog(mock_bot_without_container)
            repr_str = repr(cog_with_fallback)
            assert "BaseCog" in repr_str
            assert "injection=fallback" in repr_str

    def test_repr(self, mock_bot_with_container: Mock, mock_bot_without_container: Mock) -> None:
        """Test string representation of BaseCog."""
        def _test_repr_with_bot(bot: Mock, expected_injection: str) -> None:
            bot.user = Mock()
            bot.user.__str__ = Mock(return_value="TestBot#1234")
            cog = BaseCog(bot)  # type: ignore[arg-type]
            repr_str = repr(cog)
            assert "BaseCog" in repr_str
            assert f"injection={expected_injection}" in repr_str

        # Test with injection
        _test_repr_with_bot(mock_bot_with_container, "injected")

        # Test with fallback
        with patch('tux.core.base_cog.DatabaseController'):
            _test_repr_with_bot(mock_bot_without_container, "fallback")

    def test_service_injection_partial_failure(self, mock_bot_with_container: Mock) -> None:
        """Test BaseCog handles partial service injection failures gracefully."""
        # Make only database service injection fail
        def get_optional_side_effect(service_type: type[Any]) -> Any:
            if service_type == IDatabaseService:
                raise RuntimeError("Database service injection failed")
            return {
                IBotService: MockBotService(),
                IConfigService: MockConfigService(),
            }.get(service_type)

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

    def test_inheritance_from_commands_cog(self, mock_bot_with_container: Mock) -> None:
        """Test that BaseCog properly inherits from commands.Cog."""
        cog = BaseCog(mock_bot_with_container)

        # Verify inheritance
        assert isinstance(cog, commands.Cog)
# Test methods and other content here
        assert hasattr(cog, 'description')
