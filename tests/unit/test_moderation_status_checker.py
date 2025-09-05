"""
🚀 StatusChecker Unit Tests - User Restriction Status Checking

Tests for the StatusChecker mixin that handles checking if users are under
various moderation restrictions like jail, pollban, snippetban.

Test Coverage:
- Jail status checking
- Poll ban status checking
- Snippet ban status checking
- Database query integration
- Error handling for status checks
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from tux.services.moderation.status_checker import StatusChecker
from tux.database.models import CaseType as DBCaseType


class TestStatusChecker:
    """📊 Test StatusChecker functionality."""

    @pytest.fixture
    def status_checker(self) -> StatusChecker:
        """Create a StatusChecker instance for testing."""
        checker = StatusChecker()
        # Mock the database attribute
        checker.db = MagicMock()
        checker.db.case = MagicMock()
        checker.db.case.is_user_under_restriction = AsyncMock()
        return checker

    @pytest.mark.unit
    async def test_is_pollbanned_true(self, status_checker: StatusChecker) -> None:
        """Test checking if a user is poll banned (positive case)."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return True (user is poll banned)
        status_checker.db.case.is_user_under_restriction.return_value = True

        result = await status_checker.is_pollbanned(guild_id, user_id)

        assert result is True
        status_checker.db.case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,  # Note: This seems to be a bug in the original code
            inactive_restriction_type=DBCaseType.UNJAIL,
        )

    @pytest.mark.unit
    async def test_is_pollbanned_false(self, status_checker: StatusChecker) -> None:
        """Test checking if a user is poll banned (negative case)."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return False (user is not poll banned)
        status_checker.db.case.is_user_under_restriction.return_value = False

        result = await status_checker.is_pollbanned(guild_id, user_id)

        assert result is False
        status_checker.db.case.is_user_under_restriction.assert_called_once()

    @pytest.mark.unit
    async def test_is_snippetbanned_true(self, status_checker: StatusChecker) -> None:
        """Test checking if a user is snippet banned (positive case)."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return True (user is snippet banned)
        status_checker.db.case.is_user_under_restriction.return_value = True

        result = await status_checker.is_snippetbanned(guild_id, user_id)

        assert result is True
        status_checker.db.case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,  # Note: This seems to be a bug in the original code
            inactive_restriction_type=DBCaseType.UNJAIL,
        )

    @pytest.mark.unit
    async def test_is_snippetbanned_false(self, status_checker: StatusChecker) -> None:
        """Test checking if a user is snippet banned (negative case)."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return False (user is not snippet banned)
        status_checker.db.case.is_user_under_restriction.return_value = False

        result = await status_checker.is_snippetbanned(guild_id, user_id)

        assert result is False
        status_checker.db.case.is_user_under_restriction.assert_called_once()

    @pytest.mark.unit
    async def test_is_jailed_true(self, status_checker: StatusChecker) -> None:
        """Test checking if a user is jailed (positive case)."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return True (user is jailed)
        status_checker.db.case.is_user_under_restriction.return_value = True

        result = await status_checker.is_jailed(guild_id, user_id)

        assert result is True
        status_checker.db.case.is_user_under_restriction.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,
            inactive_restriction_type=DBCaseType.UNJAIL,
        )

    @pytest.mark.unit
    async def test_is_jailed_false(self, status_checker: StatusChecker) -> None:
        """Test checking if a user is jailed (negative case)."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return False (user is not jailed)
        status_checker.db.case.is_user_under_restriction.return_value = False

        result = await status_checker.is_jailed(guild_id, user_id)

        assert result is False
        status_checker.db.case.is_user_under_restriction.assert_called_once()

    @pytest.mark.unit
    async def test_status_checks_with_different_guilds(self, status_checker: StatusChecker) -> None:
        """Test status checks work correctly with different guild IDs."""
        guild1_id = 111111111
        guild2_id = 222222222
        user_id = 987654321

        # Mock database to return different results for different guilds
        status_checker.db.case.is_user_under_restriction.side_effect = [True, False]

        result1 = await status_checker.is_jailed(guild1_id, user_id)
        result2 = await status_checker.is_pollbanned(guild2_id, user_id)

        assert result1 is True   # User jailed in guild1
        assert result2 is False  # User not poll banned in guild2

        assert status_checker.db.case.is_user_under_restriction.call_count == 2

    @pytest.mark.unit
    async def test_status_checks_with_different_users(self, status_checker: StatusChecker) -> None:
        """Test status checks work correctly with different user IDs."""
        guild_id = 123456789
        user1_id = 111111111
        user2_id = 222222222

        # Mock database to return different results for different users
        status_checker.db.case.is_user_under_restriction.side_effect = [True, False]

        result1 = await status_checker.is_jailed(guild_id, user1_id)
        result2 = await status_checker.is_jailed(guild_id, user2_id)

        assert result1 is True   # User1 is jailed
        assert result2 is False  # User2 is not jailed

        assert status_checker.db.case.is_user_under_restriction.call_count == 2

    @pytest.mark.unit
    async def test_database_error_handling(self, status_checker: StatusChecker) -> None:
        """Test handling of database errors during status checks."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to raise an exception
        status_checker.db.case.is_user_under_restriction.side_effect = Exception("Database connection error")

        with pytest.raises(Exception, match="Database connection error"):
            await status_checker.is_jailed(guild_id, user_id)

    @pytest.mark.unit
    async def test_status_check_with_none_database(self) -> None:
        """Test status check when database is not available."""
        checker = StatusChecker()
        # Don't set up db attribute

        guild_id = 123456789
        user_id = 987654321

        # This should handle the case gracefully by returning False
        result = await checker.is_jailed(guild_id, user_id)
        assert result is False

    @pytest.mark.unit
    async def test_multiple_status_checks_same_user(self, status_checker: StatusChecker) -> None:
        """Test multiple status checks for the same user."""
        guild_id = 123456789
        user_id = 987654321

        # Mock database to return True for all checks
        status_checker.db.case.is_user_under_restriction.return_value = True

        result1 = await status_checker.is_jailed(guild_id, user_id)
        result2 = await status_checker.is_pollbanned(guild_id, user_id)
        result3 = await status_checker.is_snippetbanned(guild_id, user_id)

        assert result1 is True
        assert result2 is True
        assert result3 is True

        # Should have made 3 separate calls
        assert status_checker.db.case.is_user_under_restriction.call_count == 3

    @pytest.mark.unit
    async def test_status_check_parameters_validation(self, status_checker: StatusChecker) -> None:
        """Test that status checks handle various parameter types correctly."""
        # Test with integer IDs
        guild_id = 123456789
        user_id = 987654321

        status_checker.db.case.is_user_under_restriction.return_value = False

        result = await status_checker.is_jailed(guild_id, user_id)
        assert result is False

        # Verify the call was made with correct parameters
        call_args = status_checker.db.case.is_user_under_restriction.call_args
        assert call_args[1]['guild_id'] == guild_id
        assert call_args[1]['user_id'] == user_id
        assert call_args[1]['active_restriction_type'] == DBCaseType.JAIL
        assert call_args[1]['inactive_restriction_type'] == DBCaseType.UNJAIL

    @pytest.mark.unit
    async def test_pollban_snippetban_bug_investigation(self, status_checker: StatusChecker) -> None:
        """Test to highlight the potential bug in pollban/snippetban status checking."""
        guild_id = 123456789
        user_id = 987654321

        status_checker.db.case.is_user_under_restriction.return_value = True

        # Check that pollban and snippetban both use JAIL as active restriction type
        # This appears to be incorrect - they should probably use POLLBAN and SNIPPETBAN respectively
        await status_checker.is_pollbanned(guild_id, user_id)
        await status_checker.is_snippetbanned(guild_id, user_id)

        calls = status_checker.db.case.is_user_under_restriction.call_args_list

        # Both calls use JAIL as the active restriction type
        for call in calls:
            assert call[1]['active_restriction_type'] == DBCaseType.JAIL

        # This suggests a bug: pollban and snippetban should probably check for their own case types
        # rather than JAIL status

    @pytest.mark.unit
    async def test_status_checker_initialization(self) -> None:
        """Test StatusChecker initialization."""
        checker = StatusChecker()

        # Should be a basic object with no special initialization requirements
        assert checker is not None
        assert hasattr(checker, 'is_jailed')
        assert hasattr(checker, 'is_pollbanned')
        assert hasattr(checker, 'is_snippetbanned')

    @pytest.mark.unit
    async def test_status_checker_method_signatures(self, status_checker: StatusChecker) -> None:
        """Test that all status checker methods have correct signatures."""
        import inspect

        # Check method signatures
        jailed_sig = inspect.signature(status_checker.is_jailed)
        pollbanned_sig = inspect.signature(status_checker.is_pollbanned)
        snippetbanned_sig = inspect.signature(status_checker.is_snippetbanned)

        # All should take guild_id and user_id parameters
        assert 'guild_id' in jailed_sig.parameters
        assert 'user_id' in jailed_sig.parameters
        assert 'guild_id' in pollbanned_sig.parameters
        assert 'user_id' in pollbanned_sig.parameters
        assert 'guild_id' in snippetbanned_sig.parameters
        assert 'user_id' in snippetbanned_sig.parameters

        # All should be async methods
        assert inspect.iscoroutinefunction(status_checker.is_jailed)
        assert inspect.iscoroutinefunction(status_checker.is_pollbanned)
        assert inspect.iscoroutinefunction(status_checker.is_snippetbanned)
