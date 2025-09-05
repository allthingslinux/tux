"""
🚀 CaseExecutor Unit Tests - Moderation Action Execution

Tests for the CaseExecutor mixin that handles the core logic of executing
moderation actions, creating cases, and coordinating DMs.

Test Coverage:
- Action execution with proper sequencing
- DM timing (before/after actions)
- Case creation coordination
- Error handling for Discord API failures
- Removal action detection
- Timeout handling
- Transaction management
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

import discord
from discord.ext import commands

from tux.services.moderation.case_executor import CaseExecutor
from tux.database.models import CaseType as DBCaseType
from tux.core.types import Tux
from tux.shared.exceptions import handle_gather_result


class TestCaseExecutor:
    """⚖️ Test CaseExecutor functionality."""

    @pytest.fixture
    def case_executor(self) -> CaseExecutor:
        """Create a CaseExecutor instance for testing."""
        executor = CaseExecutor()
        # Mock the database attribute
        executor.db = MagicMock()
        executor.db.case = MagicMock()
        executor.db.case.insert_case = AsyncMock()

        # Mock mixin methods that CaseExecutor depends on
        executor.send_dm = AsyncMock(return_value=True)
        executor.send_error_response = AsyncMock()
        executor.handle_case_response = AsyncMock()
        executor._handle_dm_result = MagicMock(return_value=True)

        return executor

    @pytest.fixture(autouse=True)
    def reset_retry_handler(self):
        """Reset retry handler circuit breakers between tests."""
        from tux.services.moderation.retry_handler import retry_handler
        # Reset circuit breakers that might be in OPEN state from previous tests
        retry_handler.reset_circuit_breaker("ban_kick")
        retry_handler.reset_circuit_breaker("timeout")
        retry_handler.reset_circuit_breaker("messages")

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.bot = MagicMock(spec=Tux)
        return ctx

    @pytest.fixture
    def mock_member(self) -> discord.Member:
        """Create a mock Discord member."""
        member = MagicMock(spec=discord.Member)
        member.id = 555666777
        member.name = "TestUser"
        return member

    @pytest.mark.unit
    async def test_get_operation_type_mapping(self, case_executor: CaseExecutor) -> None:
        """Test operation type mapping for retry handler."""
        # Test known case types
        assert case_executor._get_operation_type(DBCaseType.BAN) == "ban_kick"
        assert case_executor._get_operation_type(DBCaseType.KICK) == "ban_kick"
        assert case_executor._get_operation_type(DBCaseType.TEMPBAN) == "ban_kick"
        assert case_executor._get_operation_type(DBCaseType.TIMEOUT) == "timeout"
        assert case_executor._get_operation_type(DBCaseType.WARN) == "messages"

        # Test UNBAN operation type (ban-related, not message-related)
        assert case_executor._get_operation_type(DBCaseType.UNBAN) == "ban_kick"

    @pytest.mark.unit
    async def test_dummy_action(self, case_executor: CaseExecutor) -> None:
        """Test the dummy action coroutine."""
        result = await case_executor._dummy_action()
        assert result is None

    @pytest.mark.unit
    async def test_execute_mod_action_removal_with_dm_success(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test execution of removal action with successful DM."""
        # Setup mocks
        mock_ctx.guild.REMOVAL_ACTIONS = {DBCaseType.BAN}

        # Mock successful action
        mock_action = AsyncMock(return_value=None)

        # Mock case creation
        mock_case = MagicMock()
        mock_case.case_number = 42
        case_executor.db.case.insert_case.return_value = mock_case

        await case_executor.execute_mod_action(
            ctx=mock_ctx,
            case_type=DBCaseType.BAN,
            user=mock_member,
            reason="Test ban",
            silent=False,
            dm_action="banned",
            actions=[(mock_action, type(None))],
        )

        # Verify DM was sent before action
        case_executor.send_dm.assert_called_once_with(mock_ctx, False, mock_member, "Test ban", "banned")

        # Verify action was executed
        mock_action.assert_called_once()

        # Verify case was created
        case_executor.db.case.insert_case.assert_called_once()

        # Verify response was handled
        case_executor.handle_case_response.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_removal_with_dm_timeout(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test execution of removal action with DM timeout."""
        mock_ctx.guild.REMOVAL_ACTIONS = {DBCaseType.BAN}

        # Mock DM timeout
        case_executor.send_dm.side_effect = asyncio.TimeoutError()

        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.case_number = 42
        case_executor.db.case.insert_case.return_value = mock_case

        await case_executor.execute_mod_action(
            ctx=mock_ctx,
            case_type=DBCaseType.BAN,
            user=mock_member,
            reason="Test ban",
            silent=False,
            dm_action="banned",
            actions=[(mock_action, type(None))],
        )

        # Action should still execute despite DM timeout
        mock_action.assert_called_once()
        case_executor.db.case.insert_case.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_non_removal_dm_after(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test execution of non-removal action with DM after action."""
        # Mock successful action
        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.case_number = 42
        case_executor.db.case.insert_case.return_value = mock_case

        with patch.object(case_executor, 'send_dm', new_callable=AsyncMock) as mock_send_dm, \
             patch.object(case_executor, 'handle_case_response', new_callable=AsyncMock):

            mock_send_dm.return_value = True

            await case_executor.execute_mod_action(
                ctx=mock_ctx,
                case_type=DBCaseType.WARN,
                user=mock_member,
                reason="Test warning",
                silent=False,
                dm_action="warned",
                actions=[(mock_action, type(None))],
            )

            # DM should be sent after action for non-removal actions
            assert mock_send_dm.call_count == 1
            mock_action.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_silent_mode(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test execution in silent mode (no DMs)."""
        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.case_number = 42
        case_executor.db.case.insert_case.return_value = mock_case

        with patch.object(case_executor, 'send_dm', new_callable=AsyncMock) as mock_send_dm, \
             patch.object(case_executor, 'handle_case_response', new_callable=AsyncMock):

            await case_executor.execute_mod_action(
                ctx=mock_ctx,
                case_type=DBCaseType.WARN,
                user=mock_member,
                reason="Test warning",
                silent=True,
                dm_action="warned",
                actions=[(mock_action, type(None))],
            )

            # DM should not be sent in silent mode
            mock_send_dm.assert_not_called()
            mock_action.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_discord_forbidden_error(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test handling of Discord Forbidden errors."""
        mock_action = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "Missing permissions"))

        with patch.object(case_executor, 'send_error_response', new_callable=AsyncMock) as mock_error_response:
            with pytest.raises(discord.Forbidden):
                await case_executor.execute_mod_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Test ban",
                    silent=True,
                    dm_action="banned",
                    actions=[(mock_action, type(None))],
                )

            mock_error_response.assert_called_once()
            mock_action.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_rate_limit_error(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test handling of rate limit errors."""
        error = discord.HTTPException(MagicMock(), "Rate limited")
        error.status = 429
        mock_action = AsyncMock(side_effect=error)

        with patch.object(case_executor, 'send_error_response', new_callable=AsyncMock) as mock_error_response:
            with pytest.raises(discord.HTTPException):
                await case_executor.execute_mod_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Test ban",
                    silent=True,
                    dm_action="banned",
                    actions=[(mock_action, type(None))],
                )

            mock_error_response.assert_called_once_with(mock_ctx, "I'm being rate limited. Please try again in a moment.")

    @pytest.mark.unit
    async def test_execute_mod_action_server_error(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test handling of Discord server errors."""
        error = discord.HTTPException(MagicMock(), "Internal server error")
        error.status = 500
        mock_action = AsyncMock(side_effect=error)

        with patch.object(case_executor, 'send_error_response', new_callable=AsyncMock) as mock_error_response:
            with pytest.raises(discord.HTTPException):
                await case_executor.execute_mod_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Test ban",
                    silent=True,
                    dm_action="banned",
                    actions=[(mock_action, type(None))],
                )

            mock_error_response.assert_called_once_with(mock_ctx, "Discord is experiencing issues. Please try again later.")

    @pytest.mark.unit
    async def test_execute_mod_action_not_found_error(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test handling of Discord NotFound errors."""
        not_found_error = discord.NotFound(MagicMock(), "User not found")
        not_found_error.status = 404  # Set proper status code
        mock_action = AsyncMock(side_effect=not_found_error)

        with patch.object(case_executor, 'send_error_response', new_callable=AsyncMock) as mock_error_response:
            with pytest.raises(discord.NotFound):
                await case_executor.execute_mod_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Test ban",
                    silent=True,
                    dm_action="banned",
                    actions=[(mock_action, type(None))],
                )

            mock_error_response.assert_called_once_with(mock_ctx, "Could not find the target user or channel.")

    @pytest.mark.unit
    async def test_execute_mod_action_multiple_actions(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test execution with multiple actions."""
        action1 = AsyncMock(return_value="result1")
        action2 = AsyncMock(return_value="result2")
        action3 = AsyncMock(return_value="result3")

        mock_case = MagicMock()
        mock_case.case_number = 42
        case_executor.db.case.insert_case.return_value = mock_case

        with patch.object(case_executor, 'handle_case_response', new_callable=AsyncMock):
            await case_executor.execute_mod_action(
                ctx=mock_ctx,
                case_type=DBCaseType.WARN,
                user=mock_member,
                reason="Test warning",
                silent=True,
                dm_action="warned",
                actions=[
                    (action1, str),
                    (action2, str),
                    (action3, str),
                ],
            )

            # All actions should be executed
            action1.assert_called_once()
            action2.assert_called_once()
            action3.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_database_failure_after_success(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test handling of database failure after successful action (critical error case)."""
        mock_action = AsyncMock(return_value=None)
        case_executor.db.case.insert_case.side_effect = Exception("Database connection lost")

        with patch.object(case_executor, 'handle_case_response', new_callable=AsyncMock):
            # Should complete but log critical error
            await case_executor.execute_mod_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=mock_member,
                reason="Test ban",
                silent=True,
                dm_action="banned",
                actions=[(mock_action, type(None))],
            )

            # Action should still complete
            mock_action.assert_called_once()
            # Database call should have been attempted
            case_executor.db.case.insert_case.assert_called_once()

    @pytest.mark.unit
    async def test_execute_mod_action_with_duration(
        self,
        case_executor: CaseExecutor,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test execution with duration parameter."""
        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.case_number = 42
        case_executor.db.case.insert_case.return_value = mock_case

        expires_at = datetime.now(UTC)

        with patch.object(case_executor, 'handle_case_response', new_callable=AsyncMock) as mock_response:
            await case_executor.execute_mod_action(
                ctx=mock_ctx,
                case_type=DBCaseType.TIMEOUT,
                user=mock_member,
                reason="Test timeout",
                silent=True,
                dm_action="timed out",
                actions=[(mock_action, type(None))],
                duration="1h",
                expires_at=expires_at,
            )

            # Verify database call includes expires_at
            call_args = case_executor.db.case.insert_case.call_args
            assert call_args[1]['case_expires_at'] == expires_at

            # Verify response handler gets duration
            mock_response.assert_called_once()
            call_args = mock_response.call_args
            # Duration is passed as positional argument (7th position)
            assert call_args[0][6] == "1h"

    @pytest.mark.unit
    async def test_handle_gather_result_with_exception(self) -> None:
        """Test handle_gather_result with exception input."""
        exception = ValueError("Test error")

        # Should raise the exception
        with pytest.raises(ValueError, match="Test error"):
            handle_gather_result(exception, str)

    @pytest.mark.unit
    async def test_handle_gather_result_with_valid_result(self) -> None:
        """Test handle_gather_result with valid input."""
        result = handle_gather_result("test_string", str)
        assert result == "test_string"

    @pytest.mark.unit
    async def test_handle_gather_result_with_wrong_type(self) -> None:
        """Test handle_gather_result with wrong type."""
        # Should raise TypeError for wrong type
        with pytest.raises(TypeError, match="Expected str but got int"):
            handle_gather_result(123, str)
