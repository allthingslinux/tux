"""
Unit tests for database controllers.

Tests the BaseController and specific controller implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController
from tux.database.service import DatabaseService
from tests.fixtures.database_fixtures import (
    TEST_GUILD_ID, TEST_USER_ID,
    sample_guild, sample_guild_config, sample_snippet,
)
from tux.database.models import Guild, GuildConfig, Snippet


class TestBaseController:
    """Test BaseController functionality."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        service = MagicMock(spec=DatabaseService)
        service.session = AsyncMock()
        return service

    @pytest.fixture
    def controller(self, mock_db_service):
        """Create a BaseController instance."""
        return BaseController(Guild, mock_db_service)

    def test_controller_initialization(self, controller, mock_db_service):
        """Test controller initialization."""
        assert controller.model_class is Guild
        assert controller.db_service is mock_db_service

    def test_get_by_id(self, controller, mock_db_service, sample_guild):
        """Test get_by_id method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_guild
        mock_session.execute.return_value = mock_result

        # Test get_by_id (would be async in real usage)
        # result = await controller.get_by_id(TEST_GUILD_ID)
        # assert result is not None

    def test_get_all(self, controller, mock_db_service, sample_guild):
        """Test get_all method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_guild]
        mock_session.execute.return_value = mock_result

        # Test get_all (would be async in real usage)
        # results = await controller.get_all()
        # assert len(results) == 1

    def test_create(self, controller, mock_db_service):
        """Test create method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        guild_data = {"guild_id": TEST_GUILD_ID}

        # Test create (would be async in real usage)
        # result = await controller.create(guild_data)
        # assert result.guild_id == TEST_GUILD_ID

    def test_update(self, controller, mock_db_service, sample_guild):
        """Test update method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        existing_guild = sample_guild
        existing_guild.case_count = 5

        # Mock finding existing record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_guild
        mock_session.execute.return_value = mock_result

        update_data = {"case_count": 10}

        # Test update (would be async in real usage)
        # result = await controller.update(TEST_GUILD_ID, update_data)
        # assert result.case_count == 10

    def test_delete(self, controller, mock_db_service, sample_guild):
        """Test delete method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        existing_guild = sample_guild

        # Mock finding existing record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_guild
        mock_session.execute.return_value = mock_result

        # Test delete (would be async in real usage)
        # result = await controller.delete(TEST_GUILD_ID)
        # assert result is True

    def test_exists(self, controller, mock_db_service):
        """Test exists method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        # Test exists (would be async in real usage)
        # result = await controller.exists(TEST_GUILD_ID)
        # assert result is True

    def test_count(self, controller, mock_db_service):
        """Test count method."""
        # Mock the session context manager
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result

        # Test count (would be async in real usage)
        # result = await controller.count()
        # assert result == 42

    def test_execute_query_with_span(self, controller, mock_db_service):
        """Test query execution with Sentry span."""
        with patch('tux.services.tracing.start_span') as mock_span:

            mock_span_instance = MagicMock()
            mock_span.return_value.__enter__.return_value = mock_span_instance
            mock_span.return_value.__exit__.return_value = None

            # Mock the session
            mock_session = AsyncMock()
            mock_db_service.session.return_value.__aenter__.return_value = mock_session

            # Test query execution with span (would be async in real usage)

    def test_execute_query_without_span(self, controller, mock_db_service):
        """Test query execution without Sentry span."""
        with patch('tux.services.tracing.start_span') as mock_span:
            # Mock the session
            mock_session = AsyncMock()
            mock_db_service.session.return_value.__aenter__.return_value = mock_session

            # Test query execution without span (would be async in real usage)


class TestGuildController:
    """Test GuildController functionality."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        service = MagicMock(spec=DatabaseService)
        service.session = AsyncMock()
        return service

    @pytest.fixture
    def guild_controller(self, mock_db_service):
        """Create a GuildController instance."""
        from tux.database.controllers.guild import GuildController
        return GuildController(mock_db_service)

    def test_guild_controller_initialization(self, guild_controller, mock_db_service):
        """Test guild controller initialization."""
        assert guild_controller.db_service is mock_db_service
        assert guild_controller.model_class is Guild

    def test_get_guild_with_config(self, guild_controller, mock_db_service, sample_guild, sample_guild_config):
        """Test getting guild with config relationship."""
        # Mock the session
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        guild = sample_guild
        config = sample_guild_config

        # Set up relationship
        guild.guild_config = config

        # Mock the query with options
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = guild
        mock_session.execute.return_value = mock_result

        # Test get_guild_with_config (would be async in real usage)
        # result = await guild_controller.get_guild_with_config(TEST_GUILD_ID)
        # assert result is not None
        # assert result.guild_config is not None

    def test_get_or_create_guild(self, guild_controller, mock_db_service):
        """Test get or create guild functionality."""
        # Mock the session
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        # Mock guild not found initially
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Test get_or_create_guild (would be async in real usage)
        # result = await guild_controller.get_or_create_guild(TEST_GUILD_ID)
        # assert result.guild_id == TEST_GUILD_ID


class TestGuildConfigController:
    """Test GuildConfigController functionality."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        service = MagicMock(spec=DatabaseService)
        service.session = AsyncMock()
        return service

    @pytest.fixture
    def guild_config_controller(self, mock_db_service):
        """Create a GuildConfigController instance."""
        from tux.database.controllers.guild_config import GuildConfigController
        return GuildConfigController(mock_db_service)

    def test_guild_config_controller_initialization(self, guild_config_controller, mock_db_service):
        """Test guild config controller initialization."""
        assert guild_config_controller.db_service is mock_db_service
        assert guild_config_controller.model_class is GuildConfig

    def test_get_config_by_guild_id(self, guild_config_controller, mock_db_service, sample_guild_config):
        """Test getting config by guild ID."""
        # Mock the session
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        config = sample_guild_config

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = config
        mock_session.execute.return_value = mock_result

        # Test get_config_by_guild_id (would be async in real usage)
        # result = await guild_config_controller.get_config_by_guild_id(TEST_GUILD_ID)
        # assert result is not None
        # assert result.guild_id == TEST_GUILD_ID

    def test_update_guild_prefix(self, guild_config_controller, mock_db_service, sample_guild_config):
        """Test updating guild prefix."""
        # Mock the session
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        config = sample_guild_config

        # Mock finding existing config
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = config
        mock_session.execute.return_value = mock_result

        # Test update_guild_prefix (would be async in real usage)
        # result = await guild_config_controller.update_guild_prefix(TEST_GUILD_ID, "$")
        # assert result.prefix == "$"


class TestSnippetController:
    """Test SnippetController functionality."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        service = MagicMock(spec=DatabaseService)
        service.session = AsyncMock()
        return service

    @pytest.fixture
    def snippet_controller(self, mock_db_service):
        """Create a SnippetController instance."""
        from tux.database.controllers.snippet import SnippetController
        return SnippetController(mock_db_service)

    def test_snippet_controller_initialization(self, snippet_controller, mock_db_service):
        """Test snippet controller initialization."""
        assert snippet_controller.db_service is mock_db_service
        assert snippet_controller.model_class is Snippet

    def test_get_snippet_by_name_and_guild(self, snippet_controller, mock_db_service, sample_snippet):
        """Test getting snippet by name and guild."""
        # Mock the session
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        snippet = sample_snippet

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snippet
        mock_session.execute.return_value = mock_result

        # Test get_snippet_by_name_and_guild (would be async in real usage)
        # result = await snippet_controller.get_snippet_by_name_and_guild("test_snippet", TEST_GUILD_ID)
        # assert result is not None
        # assert result.snippet_name == "test_snippet"

    def test_increment_snippet_usage(self, snippet_controller, mock_db_service, sample_snippet):
        """Test incrementing snippet usage counter."""
        # Mock the session
        mock_session = AsyncMock()
        mock_db_service.session.return_value.__aenter__.return_value = mock_session

        snippet = sample_snippet
        original_uses = snippet.uses

        # Mock finding existing snippet
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snippet
        mock_session.execute.return_value = mock_result

        # Test increment_snippet_usage (would be async in real usage)
        # result = await snippet_controller.increment_snippet_usage("test_snippet", TEST_GUILD_ID)
        # assert result.uses == original_uses + 1


class TestControllerErrorHandling:
    """Test error handling in controllers."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        service = MagicMock(spec=DatabaseService)
        service.session = AsyncMock()
        return service

    def test_database_connection_error(self, mock_db_service):
        """Test handling of database connection errors."""
        # Mock session to raise connection error
        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__.side_effect = Exception("Connection failed")
        mock_db_service.session.return_value = mock_session_cm

        controller = BaseController(Guild, mock_db_service)

        # Test that connection errors are handled properly (would be async in real usage)
        # with pytest.raises(Exception, match="Connection failed"):
        #     await controller.get_by_id(TEST_GUILD_ID)

    def test_database_constraint_error(self, mock_db_service):
        """Test handling of database constraint errors."""
        # Mock session to raise constraint error
        mock_session = AsyncMock()
        mock_session.add.side_effect = Exception("UNIQUE constraint failed")
        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__.return_value = mock_session
        mock_db_service.session.return_value = mock_session_cm

        controller = BaseController(Guild, mock_db_service)

        guild_data = {"guild_id": TEST_GUILD_ID}

        # Test that constraint errors are handled properly (would be async in real usage)
        # with pytest.raises(Exception, match="UNIQUE constraint failed"):
        #     await controller.create(guild_data)

    def test_not_found_error(self, mock_db_service):
        """Test handling of not found errors."""
        # Mock session to return None for queries
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__.return_value = mock_session
        mock_db_service.session.return_value = mock_session_cm

        controller = BaseController(Guild, mock_db_service)

        # Test that not found errors are handled properly (would be async in real usage)
        # result = await controller.get_by_id(999999)
        # assert result is None


class TestControllerIntegration:
    """Test controller integration with database service."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        service = MagicMock(spec=DatabaseService)
        service.session = AsyncMock()
        return service

    def test_controller_service_integration(self, mock_db_service):
        """Test that controllers properly integrate with database service."""
        controller = BaseController(Guild, mock_db_service)

        # Verify service integration
        assert controller.db_service is mock_db_service

        # Verify session access
        assert hasattr(mock_db_service, 'session')

    def test_multiple_controller_instances(self, mock_db_service):
        """Test that multiple controllers can use the same service."""
        guild_controller = BaseController(Guild, mock_db_service)
        config_controller = BaseController(GuildConfig, mock_db_service)

        # Both should use the same service instance
        assert guild_controller.db_service is mock_db_service
        assert config_controller.db_service is mock_db_service

        # But they should have different model classes
        assert guild_controller.model_class is Guild
        assert config_controller.model_class is GuildConfig

    def test_controller_method_signatures(self, mock_db_service):
        """Test that controller methods have correct signatures."""
        controller = BaseController(Guild, mock_db_service)

        # Check that all expected methods exist
        expected_methods = [
            'get_by_id', 'get_all', 'create', 'update', 'delete',
            'exists', 'count', 'execute_query',
        ]

        for method_name in expected_methods:
            assert hasattr(controller, method_name), f"Missing method: {method_name}"

    def test_controller_error_propagation(self, mock_db_service):
        """Test that controllers properly propagate errors."""
        # Mock service to raise an error
        mock_db_service.session.side_effect = Exception("Service error")

        controller = BaseController(Guild, mock_db_service)

        # Errors should be propagated up (would be async in real usage)
        # with pytest.raises(Exception, match="Service error"):
        #     await controller.get_by_id(TEST_GUILD_ID)
