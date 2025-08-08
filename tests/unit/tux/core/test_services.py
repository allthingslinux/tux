"""Unit tests for concrete service implementations."""

from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest

from tux.core.services import BotService, ConfigService, DatabaseService
from tux.services.database.controllers import DatabaseController


class TestDatabaseService:
    """Test cases for DatabaseService."""

    def test_initialization(self) -> None:
        """Test DatabaseService initialization."""
        service = DatabaseService()

        # Controller should be None initially (lazy loading)
        assert service._controller is None

    def test_get_controller_lazy_loading(self) -> None:
        """Test that get_controller creates controller on first access."""
        service = DatabaseService()

        controller = service.get_controller()

        assert isinstance(controller, DatabaseController)
        assert service._controller is controller

        # Second call should return same instance
        controller2 = service.get_controller()
        assert controller2 is controller

    @pytest.mark.asyncio
    async def test_execute_query_success(self) -> None:
        """Test successful query execution."""
        service = DatabaseService()

        # Mock the controller and its method
        mock_controller = Mock()
        mock_method = AsyncMock(return_value="test_result")
        mock_controller.test_operation = mock_method

        service._controller = mock_controller

        result = await service.execute_query("test_operation", arg1="value1", kwarg1="kwvalue1")

        assert result == "test_result"
        mock_method.assert_called_once_with(arg1="value1", kwarg1="kwvalue1")

    @pytest.mark.asyncio
    async def test_execute_query_nonexistent_operation(self) -> None:
        """Test query execution with nonexistent operation."""
        service = DatabaseService()

        mock_controller = Mock(spec=[])  # Empty spec means no attributes
        service._controller = mock_controller

        with pytest.raises(AttributeError, match="has no operation 'nonexistent'"):
            await service.execute_query("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_query_non_callable_attribute(self) -> None:
        """Test query execution with non-callable attribute."""
        service = DatabaseService()

        mock_controller = Mock()
        mock_controller.test_attr = "not_callable"
        service._controller = mock_controller

        result = await service.execute_query("test_attr")

        assert result == "not_callable"


class TestBotService:
    """Test cases for BotService."""

    def test_initialization(self) -> None:
        """Test BotService initialization."""
        mock_bot = Mock()
        service = BotService(mock_bot)

        assert service._bot is mock_bot

    def test_latency_property(self) -> None:
        """Test latency property."""
        mock_bot = Mock()
        mock_bot.latency = 0.123
        service = BotService(mock_bot)

        assert service.latency == 0.123

    def test_get_user_success(self) -> None:
        """Test successful user retrieval."""
        mock_bot = Mock()
        mock_user = Mock(spec=discord.User)
        mock_bot.get_user.return_value = mock_user
        service = BotService(mock_bot)

        result = service.get_user(12345)

        assert result is mock_user
        mock_bot.get_user.assert_called_once_with(12345)

    def test_get_user_not_found(self) -> None:
        """Test user retrieval when user not found."""
        mock_bot = Mock()
        mock_bot.get_user.return_value = None
        service = BotService(mock_bot)

        result = service.get_user(12345)

        assert result is None

    def test_get_user_exception(self) -> None:
        """Test user retrieval with exception."""
        mock_bot = Mock()
        mock_bot.get_user.side_effect = Exception("Test error")
        service = BotService(mock_bot)

        result = service.get_user(12345)

        assert result is None

    def test_get_emoji_success(self) -> None:
        """Test successful emoji retrieval."""
        mock_bot = Mock()
        mock_emoji = Mock(spec=discord.Emoji)
        mock_bot.get_emoji.return_value = mock_emoji
        service = BotService(mock_bot)

        result = service.get_emoji(67890)

        assert result is mock_emoji
        mock_bot.get_emoji.assert_called_once_with(67890)

    def test_get_emoji_not_found(self) -> None:
        """Test emoji retrieval when emoji not found."""
        mock_bot = Mock()
        mock_bot.get_emoji.return_value = None
        service = BotService(mock_bot)

        result = service.get_emoji(67890)

        assert result is None

    def test_get_emoji_exception(self) -> None:
        """Test emoji retrieval with exception."""
        mock_bot = Mock()
        mock_bot.get_emoji.side_effect = Exception("Test error")
        service = BotService(mock_bot)

        result = service.get_emoji(67890)

        assert result is None

    def test_user_property(self) -> None:
        """Test user property."""
        mock_bot = Mock()
        mock_client_user = Mock(spec=discord.ClientUser)
        mock_bot.user = mock_client_user
        service = BotService(mock_bot)

        assert service.user is mock_client_user

    def test_guilds_property(self) -> None:
        """Test guilds property."""
        mock_bot = Mock()
        mock_guilds = [Mock(spec=discord.Guild), Mock(spec=discord.Guild)]
        mock_bot.guilds = mock_guilds
        service = BotService(mock_bot)

        result = service.guilds

        assert result == mock_guilds
        assert isinstance(result, list)


class TestConfigService:
    """Test cases for ConfigService."""

    @patch('tux.core.services.Config')
    def test_initialization(self, mock_config_class: Mock) -> None:
        """Test ConfigService initialization."""
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        service = ConfigService()

        assert service._config is mock_config_instance
        mock_config_class.assert_called_once()

    @patch('tux.core.services.Config')
    def test_get_existing_attribute(self, mock_config_class: Mock) -> None:
        """Test getting an existing configuration attribute."""
        mock_config_instance = Mock()
        mock_config_instance.TEST_KEY = "test_value"
        mock_config_class.return_value = mock_config_instance

        service = ConfigService()
        result = service.get("TEST_KEY")

        assert result == "test_value"

    @patch('tux.core.services.Config')
    def test_get_nonexistent_attribute(self, mock_config_class: Mock) -> None:
        """Test getting a nonexistent configuration attribute."""
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        # Configure mock to not have the attribute
        del mock_config_instance.NONEXISTENT_KEY

        service = ConfigService()
        result = service.get("NONEXISTENT_KEY", "default_value")

        assert result == "default_value"

    @patch('tux.core.services.Config')
    def test_get_database_url(self, mock_config_class: Mock) -> None:
        """Test getting database URL."""
        mock_config_instance = Mock()
        mock_config_instance.DATABASE_URL = "sqlite:///test.db"
        mock_config_class.return_value = mock_config_instance

        service = ConfigService()
        result = service.get_database_url()

        assert result == "sqlite:///test.db"

    @patch('tux.core.services.Config')
    def test_get_database_url_exception(self, mock_config_class: Mock) -> None:
        """Test getting database URL with exception."""
        mock_config_instance = Mock()
        type(mock_config_instance).DATABASE_URL = property(lambda self: (_ for _ in ()).throw(Exception("Test error")))
        mock_config_class.return_value = mock_config_instance

        service = ConfigService()

        with pytest.raises(Exception, match="Test error"):
            service.get_database_url()

    @patch('tux.core.services.Config')
    def test_get_bot_token(self, mock_config_class: Mock) -> None:
        """Test getting bot token."""
        mock_config_instance = Mock()
        mock_config_instance.BOT_TOKEN = "test_token_123"
        mock_config_class.return_value = mock_config_instance

        service = ConfigService()
        result = service.get_bot_token()

        assert result == "test_token_123"

    @patch('tux.core.services.Config')
    def test_get_bot_token_exception(self, mock_config_class: Mock) -> None:
        """Test getting bot token with exception."""
        mock_config_instance = Mock()
        type(mock_config_instance).BOT_TOKEN = property(lambda self: (_ for _ in ()).throw(Exception("Token error")))
        mock_config_class.return_value = mock_config_instance

        service = ConfigService()

        with pytest.raises(Exception, match="Token error"):
            service.get_bot_token()

    @patch('tux.core.services.is_dev_mode')
    @patch('tux.core.services.Config')
    def test_is_dev_mode_true(self, mock_config_class: Mock, mock_is_dev_mode: Mock) -> None:
        """Test is_dev_mode returning True."""
        mock_config_class.return_value = Mock()
        mock_is_dev_mode.return_value = True

        service = ConfigService()
        result = service.is_dev_mode()

        assert result is True
        mock_is_dev_mode.assert_called_once()

    @patch('tux.core.services.is_dev_mode')
    @patch('tux.core.services.Config')
    def test_is_dev_mode_false(self, mock_config_class: Mock, mock_is_dev_mode: Mock) -> None:
        """Test is_dev_mode returning False."""
        mock_config_class.return_value = Mock()
        mock_is_dev_mode.return_value = False

        service = ConfigService()
        result = service.is_dev_mode()

        assert result is False

    @patch('tux.core.services.is_dev_mode')
    @patch('tux.core.services.Config')
    def test_is_dev_mode_exception(self, mock_config_class: Mock, mock_is_dev_mode: Mock) -> None:
        """Test is_dev_mode with exception."""
        mock_config_class.return_value = Mock()
        mock_is_dev_mode.side_effect = Exception("Dev mode error")

        service = ConfigService()
        result = service.is_dev_mode()

        assert result is False
