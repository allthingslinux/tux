"""Unit tests for the SnippetsBaseCog with dependency injection."""

from __future__ import annotations

from typing import Any, Dict, Optional, cast, TYPE_CHECKING
from collections.abc import AsyncGenerator
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, Mock, PropertyMock

# Import interfaces
from tux.core.interfaces import IDatabaseService, IBotService, IConfigService

# Import the SnippetsBaseCog after patching the database
with patch('tux.services.database.client.DatabaseClient'):
    from tux.modules.snippets import SnippetsBaseCog

# Import test fixtures and mocks
from tests.fixtures.dependency_injection import (
    mock_container,
    MockDatabaseService,
    MockBotService,
    MockConfigService,
)
from prisma.enums import CaseType

# Type checking imports
if TYPE_CHECKING:
    from prisma.models import Snippet
    from discord.abc import MessageableChannel
    from discord.embeds import Embed
    from discord.ext.commands import Context
    from discord.interactions import Interaction
    from discord.member import Member
    from discord.role import Role
    from discord.user import User
    from discord.guild import Guild
    from discord.channel import TextChannel
    from discord.permissions import Permissions

# Type aliases
MockBot = MagicMock
MockContext = MagicMock
MockInteraction = MagicMock
MockMessage = MagicMock
MockGuild = MagicMock
MockUser = MagicMock
MockMember = MagicMock
MockChannel = MagicMock
MockEmbed = MagicMock
MockRole = MagicMock
MockPermissions = MagicMock


@pytest.fixture
def mock_bot_fixture() -> MockBot:
    """
    Create a mock bot instance for testing.

    Returns:
        MockBot: A mocked bot instance with basic attributes.
    """
    bot = MagicMock()
    bot.user = MagicMock()
    bot.guilds = []
    return cast(MockBot, bot)


@pytest.fixture
def mock_services() -> dict[str, Any]:
    """
    Create mock services for testing.

    Returns:
        Dict[str, Any]: A dictionary containing mock services.
    """
    return {
        'db_service': MockDatabaseService(),
        'bot_service': MockBotService(),
        'config_service': MockConfigService(),
    }


@pytest.fixture
def snippets_base_cog(
    mock_bot_fixture: MockBot,
    mock_container: Any,  # Type from dependency injection
    mock_services: dict[str, Any],
) -> SnippetsBaseCog:
    """
    Create a SnippetsBaseCog instance with mocked dependencies.

    Args:
        mock_bot_fixture: Mock bot instance.
        mock_container: Mock dependency injection container.
        mock_services: Dictionary of mock services.

    Returns:
        SnippetsBaseCog: An instance of SnippetsBaseCog with mocked dependencies.
    """
    # Set up the container with mock services using register_instance
    from tux.services.database.interfaces import IDatabaseService
    from tux.services.bot.interfaces import IBotService
    from tux.services.config.interfaces import IConfigService

    # Register the mock services with the container
    mock_container.register_instance(IDatabaseService, mock_services['db_service'])
    mock_container.register_instance(IBotService, mock_services['bot_service'])
    mock_container.register_instance(IConfigService, mock_services['config_service'])

    # Attach the container to the mock bot
    mock_bot_fixture.container = mock_container
    return SnippetsBaseCog(mock_bot_fixture)


@pytest.mark.asyncio
class TestSnippetsBaseCog:
    """Test cases for the SnippetsBaseCog."""

    async def test_cog_initialization(self, snippets_base_cog: SnippetsBaseCog) -> None:
        """
        Test that the cog initializes correctly with dependency injection.

        Args:
            snippets_base_cog: An instance of SnippetsBaseCog with mocked dependencies.
        """
        assert snippets_base_cog.bot is not None
        assert hasattr(snippets_base_cog.bot, 'container')
        assert snippets_base_cog.bot.container is not None
        assert snippets_base_cog.db_service is not None
        assert hasattr(snippets_base_cog, 'db')  # Backward compatibility

    @pytest.mark.asyncio
    async def test_is_snippetbanned_true(
        self,
        snippets_base_cog: SnippetsBaseCog,
    ) -> None:
        """Test is_snippetbanned returns True when user is banned."""
        guild_id = 12345
        user_id = 67890

        # Mock database to return True (user is banned)
        snippets_base_cog.db.case.is_user_under_restriction = AsyncMock(return_value=True)

        result = await snippets_base_cog.is_snippetbanned(guild_id, user_id)

        assert result is True
        snippets_base_cog.db.case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.SNIPPETBAN,
            inactive_restriction_type=CaseType.SNIPPETUNBAN,
        )

    @pytest.mark.asyncio
    async def test_is_snippetbanned_false(self, snippets_base_cog: SnippetsBaseCog) -> None:
        """Test is_snippetbanned returns False when user is not banned."""
        guild_id = 12345
        user_id = 67890

        # Mock database to return False (user is not banned)
        snippets_base_cog.db.case.is_user_under_restriction = AsyncMock(return_value=False)

        result = await snippets_base_cog.is_snippetbanned(guild_id, user_id)

        assert result is False

    def test_create_snippets_list_embed_empty(self, snippets_base_cog: SnippetsBaseCog) -> None:
        """Test creating embed for empty snippets list."""
        # Mock context
        ctx = Mock()
        ctx.author = Mock()
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            result = snippets_base_cog._create_snippets_list_embed(ctx, [], 0)

            assert result == mock_embed
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert call_args['description'] == "No snippets found."

    def test_create_snippets_list_embed_with_snippets(self, snippets_base_cog):
        """Test creating embed with snippets list."""
        # Mock context
        ctx = Mock()
        ctx.author = Mock()
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.guild = Mock()
        ctx.guild.name = "TestGuild"
        ctx.guild.icon = Mock()
        ctx.guild.icon.url = "http://example.com/guild_icon.png"
        ctx.message = Mock()
        ctx.message.created_at = Mock()
        ctx.bot = Mock()

        # Mock snippets
        snippet1 = Mock()
        snippet1.snippet_name = "test1"
        snippet1.uses = 5
        snippet1.locked = False
        snippet1.alias = False

        snippet2 = Mock()
        snippet2.snippet_name = "test2"
        snippet2.uses = 10
        snippet2.locked = True
        snippet2.alias = True

        snippets = [snippet1, snippet2]

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            with patch('tux.ui.embeds.EmbedCreator.get_footer', return_value=("Footer", "footer_url")):
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                result = snippets_base_cog._create_snippets_list_embed(ctx, snippets, 10)

                assert result == mock_embed
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert call_args['title'] == "Snippets (2/10)"
                assert "test1" in call_args['description']
                assert "test2" in call_args['description']
                assert "🔒" in call_args['description']  # Locked indicator

    async def test_check_if_user_has_mod_override_true(self, snippets_base_cog):
        """Test mod override check when user has permissions."""
        # Mock context
        ctx = Mock()

        with patch('tux.utils.checks.has_pl') as mock_has_pl:
            mock_check = Mock()
            mock_check.predicate = AsyncMock()  # No exception = has permission
            mock_has_pl.return_value = mock_check

            result = await snippets_base_cog.check_if_user_has_mod_override(ctx)

            assert result is True
            mock_has_pl.assert_called_once_with(2)
            mock_check.predicate.assert_called_once_with(ctx)

    async def test_check_if_user_has_mod_override_false(self, snippets_base_cog):
        """Test mod override check when user lacks permissions."""
        from discord.ext import commands

        # Mock context
        ctx = Mock()

        with patch('tux.utils.checks.has_pl') as mock_has_pl:
            mock_check = Mock()
            mock_check.predicate = AsyncMock(side_effect=commands.CheckFailure("No permission"))
            mock_has_pl.return_value = mock_check

            result = await snippets_base_cog.check_if_user_has_mod_override(ctx)

            assert result is False

    async def test_check_if_user_has_mod_override_exception(self, snippets_base_cog):
        """Test mod override check when unexpected exception occurs."""
        # Mock context
        ctx = Mock()

        with patch('tux.utils.checks.has_pl') as mock_has_pl:
            mock_check = Mock()
            mock_check.predicate = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_has_pl.return_value = mock_check

            with patch('loguru.logger.error') as mock_logger:
                result = await snippets_base_cog.check_if_user_has_mod_override(ctx)

                assert result is False
                mock_logger.assert_called_once()

    async def test_snippet_check_mod_override(self, snippets_base_cog):
        """Test snippet check with mod override."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()

        snippets_base_cog.check_if_user_has_mod_override = AsyncMock(return_value=True)

        result, reason = await snippets_base_cog.snippet_check(ctx)

        assert result is True
        assert reason == "Mod override granted."

    async def test_snippet_check_snippetbanned(self, snippets_base_cog):
        """Test snippet check when user is snippet banned."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890

        snippets_base_cog.check_if_user_has_mod_override = AsyncMock(return_value=False)
        snippets_base_cog.is_snippetbanned = AsyncMock(return_value=True)

        result, reason = await snippets_base_cog.snippet_check(ctx)

        assert result is False
        assert reason == "You are banned from using snippets."

    async def test_snippet_check_role_restriction(self, snippets_base_cog):
        """Test snippet check with role restrictions."""
        import discord

        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock(spec=discord.Member)
        ctx.author.id = 67890

        # Mock roles without required role
        role1 = Mock()
        role1.id = 11111
        role2 = Mock()
        role2.id = 22222
        ctx.author.roles = [role1, role2]

        snippets_base_cog.check_if_user_has_mod_override = AsyncMock(return_value=False)
        snippets_base_cog.is_snippetbanned = AsyncMock(return_value=False)

        with patch('tux.utils.config.Config') as mock_config:
            mock_config.LIMIT_TO_ROLE_IDS = True
            mock_config.ACCESS_ROLE_IDS = [33333, 44444]  # Required roles not in user's roles

            result, reason = await snippets_base_cog.snippet_check(ctx)

            assert result is False
            assert "You do not have a role" in reason
            assert "<@&33333>" in reason
            assert "<@&44444>" in reason

    async def test_snippet_check_locked_snippet(self, snippets_base_cog):
        """Test snippet check with locked snippet."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890

        snippets_base_cog.check_if_user_has_mod_override = AsyncMock(return_value=False)
        snippets_base_cog.is_snippetbanned = AsyncMock(return_value=False)

        with patch('tux.utils.config.Config') as mock_config:
            mock_config.LIMIT_TO_ROLE_IDS = False

            result, reason = await snippets_base_cog.snippet_check(ctx, snippet_locked=True)

            assert result is False
            assert reason == "This snippet is locked. You cannot edit or delete it."

    async def test_snippet_check_wrong_owner(self, snippets_base_cog):
        """Test snippet check when user is not the snippet owner."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890

        snippets_base_cog.check_if_user_has_mod_override = AsyncMock(return_value=False)
        snippets_base_cog.is_snippetbanned = AsyncMock(return_value=False)

        with patch('tux.utils.config.Config') as mock_config:
            mock_config.LIMIT_TO_ROLE_IDS = False

            result, reason = await snippets_base_cog.snippet_check(ctx, snippet_user_id=99999)

            assert result is False
            assert reason == "You can only edit or delete your own snippets."

    async def test_snippet_check_success(self, snippets_base_cog):
        """Test successful snippet check."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890

        snippets_base_cog.check_if_user_has_mod_override = AsyncMock(return_value=False)
        snippets_base_cog.is_snippetbanned = AsyncMock(return_value=False)

        with patch('tux.utils.config.Config') as mock_config:
            mock_config.LIMIT_TO_ROLE_IDS = False

            result, reason = await snippets_base_cog.snippet_check(ctx, snippet_user_id=67890)

            assert result is True
            assert reason == "All checks passed."

    async def test_get_snippet_or_error_found(self, snippets_base_cog):
        """Test getting snippet when it exists."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345

        # Mock snippet
        mock_snippet = Mock()
        snippets_base_cog.db.snippet.get_snippet_by_name_and_guild_id = AsyncMock(return_value=mock_snippet)

        result = await snippets_base_cog._get_snippet_or_error(ctx, "test_snippet")

        assert result == mock_snippet
        snippets_base_cog.db.snippet.get_snippet_by_name_and_guild_id.assert_called_once_with(
            "test_snippet", 12345,
        )

    async def test_get_snippet_or_error_not_found(self, snippets_base_cog):
        """Test getting snippet when it doesn't exist."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345

        snippets_base_cog.db.snippet.get_snippet_by_name_and_guild_id = AsyncMock(return_value=None)
        snippets_base_cog.send_snippet_error = AsyncMock()

        result = await snippets_base_cog._get_snippet_or_error(ctx, "nonexistent")

        assert result is None
        snippets_base_cog.send_snippet_error.assert_called_once_with(ctx, description="Snippet not found.")

    async def test_send_snippet_error(self, snippets_base_cog):
        """Test sending snippet error embed."""
        # Mock context
        ctx = Mock()
        ctx.author = Mock()
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.send = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            with patch('tux.shared.constants.CONST') as mock_const:
                mock_const.DEFAULT_DELETE_AFTER = 30
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                await snippets_base_cog.send_snippet_error(ctx, "Test error message")

                # Verify embed creation
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert call_args['description'] == "Test error message"

                # Verify message sent
                ctx.send.assert_called_once_with(embed=mock_embed, delete_after=30)

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        cog = SnippetsBaseCog(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, snippets_base_cog):
        """Test the string representation of the cog."""
        repr_str = repr(snippets_base_cog)
        assert "SnippetsBaseCog" in repr_str
        assert "injection=" in repr_str
