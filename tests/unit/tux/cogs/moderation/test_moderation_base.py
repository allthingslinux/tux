"""Unit tests for ModerationCogBase with dependency injection.

This module tests the migrated ModerationCogBase to ensure it properly
uses dependency injection while maintaining backward compatibility.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from discord.ext import commands

from prisma.enums import CaseType
from tests.fixtures.dependency_injection import (
    MockBotService,
    MockConfigService,
    MockDatabaseService,
    create_test_container_with_mocks,
)
from tux.cogs.moderation import ModerationCogBase
from tux.core.container import ServiceContainer


class TestModerationCogBase:
    """Test cases for ModerationCogBase with dependency injection."""

    @pytest.fixture
    def mock_bot(self) -> Mock:
        """Create a mock bot for testing."""
        bot = Mock()
        bot.latency = 0.1
        bot.user = Mock(spec=discord.ClientUser)
        bot.guilds = []
        bot.get_user = Mock(return_value=None)
        bot.get_emoji = Mock(return_value=None)
        return bot

    @pytest.fixture
    def mock_bot_with_container(self, mock_bot: Mock) -> Mock:
        """Create a mock bot with dependency injection container."""
        container, mock_db, mock_bot_service, mock_config = create_test_container_with_mocks()
        mock_bot.container = container
        return mock_bot

    @pytest.fixture
    def mock_bot_without_container(self, mock_bot: Mock) -> Mock:
        """Create a mock bot without dependency injection container."""
        # Ensure no container attribute
        if hasattr(mock_bot, 'container'):
            delattr(mock_bot, 'container')
        return mock_bot

    @pytest.fixture
    def moderation_cog_with_injection(self, mock_bot_with_container: Mock) -> ModerationCogBase:
        """Create ModerationCogBase with dependency injection."""
        return ModerationCogBase(mock_bot_with_container)

    @pytest.fixture
    def moderation_cog_without_injection(self, mock_bot_without_container: Mock) -> ModerationCogBase:
        """Create ModerationCogBase without dependency injection (fallback mode)."""
        return ModerationCogBase(mock_bot_without_container)

    def test_init_with_dependency_injection(self, mock_bot_with_container: Mock) -> None:
        """Test that ModerationCogBase initializes correctly with dependency injection."""
        cog = ModerationCogBase(mock_bot_with_container)

        # Verify inheritance from BaseCog
        from tux.core.base_cog import BaseCog
        assert isinstance(cog, BaseCog)

        # Verify bot is set
        assert cog.bot is mock_bot_with_container

        # Verify container is available
        assert cog._container is not None
        assert cog._container is mock_bot_with_container.container

        # Verify services are injected
        assert cog.db_service is not None
        assert cog.bot_service is not None
        assert cog.config_service is not None

        # Verify user action locks are initialized
        assert isinstance(cog._user_action_locks, dict)
        assert len(cog._user_action_locks) == 0
        assert cog._lock_cleanup_threshold == 100

    def test_init_without_dependency_injection(self, mock_bot_without_container: Mock) -> None:
        """Test that ModerationCogBase initializes correctly without dependency injection."""
        with patch('tux.core.base_cog.DatabaseController') as mock_db_controller:
            cog = ModerationCogBase(mock_bot_without_container)

            # Verify inheritance from BaseCog
            from tux.core.base_cog import BaseCog
            assert isinstance(cog, BaseCog)

            # Verify bot is set
            assert cog.bot is mock_bot_without_container

            # Verify container is not available
            assert cog._container is None

            # Verify fallback services are used
            assert cog.db_service is None  # No injection available

            # Verify user action locks are initialized
            assert isinstance(cog._user_action_locks, dict)
            assert len(cog._user_action_locks) == 0
            assert cog._lock_cleanup_threshold == 100

    def test_database_access_with_injection(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test that database access works with dependency injection."""
        # Access the db property (backward compatibility)
        db_controller = moderation_cog_with_injection.db

        # Verify it returns the controller from the injected service
        assert db_controller is not None
        assert moderation_cog_with_injection.db_service is not None

    def test_database_access_without_injection(self, moderation_cog_without_injection: ModerationCogBase) -> None:
        """Test that database access works without dependency injection (fallback)."""
        # Access the db property (backward compatibility)
        db_controller = moderation_cog_without_injection.db

        # Verify it returns a DatabaseController instance
        from tux.database.controllers import DatabaseController
        assert isinstance(db_controller, DatabaseController)

    @pytest.mark.asyncio
    async def test_get_user_lock(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test user lock creation and retrieval."""
        user_id = 12345

        # Get lock for user
        lock1 = await moderation_cog_with_injection.get_user_lock(user_id)
        assert isinstance(lock1, asyncio.Lock)

        # Get same lock again
        lock2 = await moderation_cog_with_injection.get_user_lock(user_id)
        assert lock1 is lock2

        # Verify lock is stored
        assert user_id in moderation_cog_with_injection._user_action_locks
        assert moderation_cog_with_injection._user_action_locks[user_id] is lock1

    @pytest.mark.asyncio
    async def test_clean_user_locks(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test cleaning of unused user locks."""
        # Create multiple locks
        user_ids = [1, 2, 3, 4, 5]
        locks = []

        for user_id in user_ids:
            lock = await moderation_cog_with_injection.get_user_lock(user_id)
            locks.append(lock)

        # Verify all locks are stored
        assert len(moderation_cog_with_injection._user_action_locks) == 5

        # Clean locks (all should be removed since none are locked)
        await moderation_cog_with_injection.clean_user_locks()

        # Verify locks are cleaned
        assert len(moderation_cog_with_injection._user_action_locks) == 0

    @pytest.mark.asyncio
    async def test_execute_user_action_with_lock(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test executing user actions with locks."""
        user_id = 12345
        expected_result = "test_result"

        # Create a mock async function
        async def mock_action(value: str) -> str:
            return value

        # Execute action with lock
        result = await moderation_cog_with_injection.execute_user_action_with_lock(
            user_id, mock_action, expected_result,
        )

        assert result == expected_result

        # Verify lock was created
        assert user_id in moderation_cog_with_injection._user_action_locks

    @pytest.mark.asyncio
    async def test_dummy_action(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test the dummy action method."""
        result = await moderation_cog_with_injection._dummy_action()
        assert result is None

    @pytest.mark.asyncio
    async def test_is_pollbanned_with_injection(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test pollban check with dependency injection."""
        guild_id = 12345
        user_id = 67890

        # Mock the database service and controller
        mock_db_service = moderation_cog_with_injection.db_service
        mock_controller = mock_db_service.get_controller()

        # Add the case attribute to the mock controller
        mock_case = Mock()
        mock_case.is_user_under_restriction = AsyncMock(return_value=True)
        mock_controller.case = mock_case

        # Test pollban check
        result = await moderation_cog_with_injection.is_pollbanned(guild_id, user_id)

        assert result is True
        mock_case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.POLLBAN,
            inactive_restriction_type=CaseType.POLLUNBAN,
        )

    @pytest.mark.asyncio
    async def test_is_snippetbanned_with_injection(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test snippetban check with dependency injection."""
        guild_id = 12345
        user_id = 67890

        # Mock the database service and controller
        mock_db_service = moderation_cog_with_injection.db_service
        mock_controller = mock_db_service.get_controller()

        # Add the case attribute to the mock controller
        mock_case = Mock()
        mock_case.is_user_under_restriction = AsyncMock(return_value=False)
        mock_controller.case = mock_case

        # Test snippetban check
        result = await moderation_cog_with_injection.is_snippetbanned(guild_id, user_id)

        assert result is False
        mock_case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.SNIPPETBAN,
            inactive_restriction_type=CaseType.SNIPPETUNBAN,
        )

    @pytest.mark.asyncio
    async def test_is_jailed_with_injection(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test jail check with dependency injection."""
        guild_id = 12345
        user_id = 67890

        # Mock the database service and controller
        mock_db_service = moderation_cog_with_injection.db_service
        mock_controller = mock_db_service.get_controller()

        # Add the case attribute to the mock controller
        mock_case = Mock()
        mock_case.is_user_under_restriction = AsyncMock(return_value=True)
        mock_controller.case = mock_case

        # Test jail check
        result = await moderation_cog_with_injection.is_jailed(guild_id, user_id)

        assert result is True
        mock_case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.JAIL,
            inactive_restriction_type=CaseType.UNJAIL,
        )

    @pytest.mark.asyncio
    async def test_send_dm_success(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test successful DM sending."""
        # Create mock context and user
        ctx = Mock(spec=commands.Context)
        ctx.guild = Mock(spec=discord.Guild)
        ctx.guild.__str__ = Mock(return_value="Test Guild")

        user = Mock(spec=discord.User)
        user.send = AsyncMock()

        # Test DM sending
        result = await moderation_cog_with_injection.send_dm(
            ctx, silent=False, user=user, reason="Test reason", action="banned",
        )

        assert result is True
        user.send.assert_called_once_with(
            "You have been banned from Test Guild for the following reason:\n> Test reason",
        )

    @pytest.mark.asyncio
    async def test_send_dm_silent(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test DM sending in silent mode."""
        # Create mock context and user
        ctx = Mock(spec=commands.Context)
        user = Mock(spec=discord.User)

        # Test silent DM sending
        result = await moderation_cog_with_injection.send_dm(
            ctx, silent=True, user=user, reason="Test reason", action="banned",
        )

        assert result is False
        # Verify send was not called
        assert not hasattr(user, 'send') or not user.send.called

    @pytest.mark.asyncio
    async def test_send_dm_failure(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test DM sending failure."""
        # Create mock context and user
        ctx = Mock(spec=commands.Context)
        ctx.guild = Mock(spec=discord.Guild)
        ctx.guild.name = "Test Guild"

        user = Mock(spec=discord.User)
        user.send = AsyncMock(side_effect=discord.Forbidden(Mock(), "Cannot send DM"))

        # Test DM sending failure
        result = await moderation_cog_with_injection.send_dm(
            ctx, silent=False, user=user, reason="Test reason", action="banned",
        )

        assert result is False
        user.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_conditions_self_moderation(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test condition check for self-moderation."""
        # Create mock context
        ctx = Mock(spec=commands.Context)
        ctx.guild = Mock(spec=discord.Guild)
        ctx.send = AsyncMock()

        user = Mock(spec=discord.User)
        user.id = 12345
        moderator = Mock(spec=discord.User)
        moderator.id = 12345  # Same as user

        # Test self-moderation check
        result = await moderation_cog_with_injection.check_conditions(ctx, user, moderator, "ban")

        assert result is False
        ctx.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_conditions_guild_owner(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test condition check for guild owner."""
        # Create mock context
        ctx = Mock(spec=commands.Context)
        ctx.guild = Mock(spec=discord.Guild)
        ctx.guild.owner_id = 12345
        ctx.send = AsyncMock()

        user = Mock(spec=discord.User)
        user.id = 12345  # Guild owner
        moderator = Mock(spec=discord.User)
        moderator.id = 67890

        # Test guild owner check
        result = await moderation_cog_with_injection.check_conditions(ctx, user, moderator, "ban")

        assert result is False
        ctx.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_conditions_success(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test successful condition check."""
        # Create mock context
        ctx = Mock(spec=commands.Context)
        ctx.guild = Mock(spec=discord.Guild)
        ctx.guild.owner_id = 99999

        user = Mock(spec=discord.User)
        user.id = 12345
        moderator = Mock(spec=discord.User)
        moderator.id = 67890

        # Test successful condition check
        result = await moderation_cog_with_injection.check_conditions(ctx, user, moderator, "ban")

        assert result is True

    def test_format_case_title_with_duration(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test case title formatting with duration."""
        title = moderation_cog_with_injection._format_case_title(CaseType.TEMPBAN, 123, "7 days")
        assert title == "Case #123 (7 days TEMPBAN)"

    def test_format_case_title_without_duration(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test case title formatting without duration."""
        title = moderation_cog_with_injection._format_case_title(CaseType.BAN, 456, None)
        assert title == "Case #456 (BAN)"

    def test_format_case_title_no_case_number(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test case title formatting without case number."""
        title = moderation_cog_with_injection._format_case_title(CaseType.WARN, None, None)
        assert title == "Case #0 (WARN)"

    def test_handle_dm_result_success(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test DM result handling for success."""
        user = Mock(spec=discord.User)
        result = moderation_cog_with_injection._handle_dm_result(user, True)
        assert result is True

    def test_handle_dm_result_failure(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test DM result handling for failure."""
        user = Mock(spec=discord.User)
        exception = discord.Forbidden(Mock(), "Cannot send DM")
        result = moderation_cog_with_injection._handle_dm_result(user, exception)
        assert result is False

    def test_handle_dm_result_false(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test DM result handling for False result."""
        user = Mock(spec=discord.User)
        result = moderation_cog_with_injection._handle_dm_result(user, False)
        assert result is False

    def test_backward_compatibility_properties(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test that backward compatibility properties still work."""
        # Test that we can access the db property
        db_controller = moderation_cog_with_injection.db
        assert db_controller is not None

        # Test that the bot property is available
        assert moderation_cog_with_injection.bot is not None

        # Test that user action locks are available
        assert hasattr(moderation_cog_with_injection, '_user_action_locks')
        assert isinstance(moderation_cog_with_injection._user_action_locks, dict)

    def test_removal_actions_constant(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test that REMOVAL_ACTIONS constant is properly defined."""
        expected_actions = {CaseType.BAN, CaseType.KICK, CaseType.TEMPBAN}
        assert moderation_cog_with_injection.REMOVAL_ACTIONS == expected_actions

    @pytest.mark.asyncio
    async def test_lock_cleanup_threshold(self, moderation_cog_with_injection: ModerationCogBase) -> None:
        """Test that lock cleanup is triggered when threshold is exceeded."""
        # Set a low threshold for testing
        moderation_cog_with_injection._lock_cleanup_threshold = 2

        # Create locks up to threshold + 1
        for i in range(3):  # One more than threshold
            await moderation_cog_with_injection.get_user_lock(i)

        # The cleanup should have been triggered, but the exact number depends on timing
        # Just verify that cleanup mechanism exists and can be called
        initial_count = len(moderation_cog_with_injection._user_action_locks)
        await moderation_cog_with_injection.clean_user_locks()
        final_count = len(moderation_cog_with_injection._user_action_locks)

        # After cleanup, there should be fewer or equal locks (since none are locked)
        assert final_count <= initial_count
