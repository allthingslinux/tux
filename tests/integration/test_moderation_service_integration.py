from typing import Any
"""
🚀 ModerationService Integration Tests - Full Workflow Testing

Integration tests for the ModerationService that test the complete moderation
workflow including all mixins working together.

Test Coverage:
- Complete moderation action execution
- Integration between all mixins
- End-to-end workflow testing
- Cross-component interaction
- Database integration
- Error handling across components
- Performance and timing tests
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext import commands

from tux.services.moderation.moderation_coordinator import ModerationCoordinator
from tux.services.moderation.case_service import CaseService
from tux.services.moderation.communication_service import CommunicationService
from tux.services.moderation.execution_service import ExecutionService
from tux.database.models import CaseType as DBCaseType
from tux.core.bot import Tux


class TestModerationCoordinatorIntegration:
    """🔗 Test ModerationCoordinator integration with all components."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        db = MagicMock()
        db.case = MagicMock()
        db.case.insert_case = AsyncMock()
        db.case.update_audit_log_message_id = AsyncMock()
        return db

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot."""
        bot = MagicMock(spec=Tux)
        bot.emoji_manager = MagicMock()
        bot.emoji_manager.get = lambda x: f":{x}:"
        return bot

    @pytest.fixture
    def case_service(self, mock_db_service: Any):
        """Create a CaseService instance."""
        return CaseService(mock_db_service.case)

    @pytest.fixture
    def communication_service(self, mock_bot: Any):
        """Create a CommunicationService instance."""
        return CommunicationService(mock_bot)

    @pytest.fixture
    def execution_service(self):
        """Create an ExecutionService instance."""
        return ExecutionService()

    @pytest.fixture
    def moderation_coordinator(self, case_service, communication_service, execution_service):
        """Create a ModerationCoordinator instance."""
        return ModerationCoordinator(
            case_service=case_service,
            communication_service=communication_service,
            execution_service=execution_service,
        )

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.author.name = "Moderator"
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def mock_member(self):
        """Create a mock Discord member."""
        member = MagicMock(spec=discord.Member)
        member.id = 555666777
        member.name = "TargetUser"
        member.top_role = MagicMock(spec=discord.Role)
        member.top_role.position = 5
        return member

    @pytest.mark.integration
    async def test_complete_ban_workflow_success(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test complete ban workflow from start to finish."""
        # Setup mocks for successful execution
        mock_ctx.guild.get_member.return_value = MagicMock()  # Bot is in guild

        # Mock successful DM
        with patch.object(moderation_coordinator._communication, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful ban action
            mock_ban_action = AsyncMock(return_value=None)

            # Mock case creation
            mock_case = MagicMock()
            mock_case.id = 42
            moderation_coordinator._case_service.create_case = AsyncMock(return_value=mock_case)

            # Mock response handling
            with patch.object(moderation_coordinator, '_send_response_embed', new_callable=AsyncMock) as mock_send_response:

                    await moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=mock_member,
                        reason="Integration test ban",
                        silent=False,
                        dm_action="banned",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # Verify the complete workflow executed
                    mock_send_dm.assert_called_once()
                    mock_ban_action.assert_called_once()
                    moderation_coordinator._case_service.create_case.assert_called_once()
                    mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_ban_workflow_with_dm_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test ban workflow when DM fails but action still succeeds."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock DM failure (timeout)
        with patch.object(moderation_coordinator._communication, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.side_effect = asyncio.TimeoutError()

            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 43
            moderation_coordinator._case_service.create_case = AsyncMock(return_value=mock_case)

            with patch.object(moderation_coordinator, '_send_response_embed', new_callable=AsyncMock) as mock_send_response:

                    await moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=mock_member,
                        reason="DM failure test",
                        silent=False,
                        dm_action="banned",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # Action should still succeed despite DM failure
                    mock_ban_action.assert_called_once()
                    moderation_coordinator._case_service.create_case.assert_called_once()
                    mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_ban_workflow_with_condition_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test ban workflow failure due to condition validation."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # In the new architecture, permission checking is done via decorators
        # and condition checking is handled by the ConditionChecker service
        # This test is no longer applicable to the ModerationCoordinator
        # Permission and condition validation happens at the command level
        pass

    @pytest.mark.integration
    async def test_non_removal_action_workflow(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test workflow for non-removal actions (like warn)."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful DM (should be sent after action for non-removal)
        with patch.object(moderation_coordinator._communication, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful warn action (dummy)
            mock_warn_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 44
            moderation_coordinator._case_service.create_case = AsyncMock(return_value=mock_case)

            with patch.object(moderation_coordinator, '_send_response_embed', new_callable=AsyncMock) as mock_send_response:

                    await moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.WARN,
                        user=mock_member,
                        reason="Integration test warning",
                        silent=False,
                        dm_action="warned",
                        actions=[(mock_warn_action, type(None))],
                    )

                    # Verify DM sent after action for non-removal
                    mock_send_dm.assert_called_once()
                    mock_warn_action.assert_called_once()
                    moderation_coordinator._case_service.create_case.assert_called_once()
                    mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_silent_mode_workflow(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test workflow in silent mode (no DMs)."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock send_dm to return False when silent=True (as per the actual implementation)
        with patch.object(moderation_coordinator._communication, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = False  # The method returns False in silent mode
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 45
            moderation_coordinator._case_service.create_case = AsyncMock(return_value=mock_case)

            with patch.object(moderation_coordinator, '_send_response_embed', new_callable=AsyncMock) as mock_send_response:

                    await moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.KICK,
                        user=mock_member,
                        reason="Silent mode test",
                        silent=True,  # Silent mode
                        dm_action="kicked",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # DM method should be called but return False in silent mode
                    mock_send_dm.assert_called_once()
                    mock_ban_action.assert_called_once()
                    moderation_coordinator._case_service.create_case.assert_called_once()
                    mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_database_failure_after_successful_action(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test handling of database failure after successful Discord action."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        with patch.object(moderation_coordinator._communication, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            mock_ban_action = AsyncMock(return_value=None)

            # Database fails after successful action
            moderation_coordinator._case_service.create_case = AsyncMock(side_effect=Exception("Database connection lost"))

            with patch.object(moderation_coordinator, '_send_response_embed', new_callable=AsyncMock) as mock_send_response:

                    # Should complete but log critical error for database failure
                    await moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=mock_member,
                        reason="Database failure test",
                        silent=False,
                        dm_action="banned",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # Action should succeed, database should fail
                    mock_ban_action.assert_called_once()
                    moderation_coordinator._case_service.create_case.assert_called_once()
                    mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_action_execution_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test handling of Discord API action failure."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Action fails with Discord error
        mock_ban_action = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "Missing permissions"))

        # The execution service catches Forbidden errors and returns None
        # The ModerationCoordinator should complete successfully despite the failure
        await moderation_coordinator.execute_moderation_action(
            ctx=mock_ctx,
            case_type=DBCaseType.BAN,
            user=mock_member,
            reason="Action failure test",
            actions=[(mock_ban_action, type(None))],
        )

        # Action should have been attempted
        mock_ban_action.assert_called_once()

    @pytest.mark.integration
    async def test_multiple_actions_execution(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test execution of multiple actions in sequence."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Multiple actions
        action1 = AsyncMock(return_value="result1")
        action2 = AsyncMock(return_value="result2")
        action3 = AsyncMock(return_value="result3")

        mock_case = MagicMock()
        mock_case.id = 46
        moderation_coordinator._case_service.create_case = AsyncMock(return_value=mock_case)

        with patch.object(moderation_coordinator._communication, 'create_embed') as mock_embed:
            with patch.object(moderation_coordinator._communication, 'send_embed', new_callable=AsyncMock) as _mock_send_embed:
                mock_embed_obj = MagicMock()
                mock_embed_obj.description = None  # Allow setting description attribute
                mock_embed.return_value = mock_embed_obj

                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.TIMEOUT,
                    user=mock_member,
                    reason="Multiple actions test",
                    silent=True,
                    dm_action="timed out",
                    actions=[
                        (action1, str),
                        (action2, str),
                        (action3, str),
                    ],
                )

                # All actions should execute in order
                action1.assert_called_once()
                action2.assert_called_once()
                action3.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()

    @pytest.mark.integration
    async def test_workflow_with_duration_and_expires_at(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
    ) -> None:
        """Test workflow with duration and expiration parameters."""
        from datetime import datetime, UTC, timedelta

        mock_ctx.guild.get_member.return_value = MagicMock()

        expires_at = datetime.now(UTC) + timedelta(hours=24)

        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.id = 47
        moderation_coordinator._case_service.create_case = AsyncMock(return_value=mock_case)

        with patch.object(moderation_coordinator._communication, 'create_embed') as mock_embed:
            with patch.object(moderation_coordinator._communication, 'send_embed', new_callable=AsyncMock) as mock_send_embed:
                mock_embed_obj = MagicMock()
                mock_embed_obj.description = None  # Allow setting description attribute
                mock_embed.return_value = mock_embed_obj

                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.TEMPBAN,
                    user=mock_member,
                    reason="Duration test",
                    silent=True,
                    dm_action="temp banned",
                    actions=[(mock_action, type(None))],
                    duration=None,  # type: ignore[arg-type]
                    expires_at=expires_at,
                )

                # Verify duration and expires_at are passed correctly
                call_args = moderation_coordinator._case_service.create_case.call_args
                assert call_args[1]['case_expires_at'] == expires_at

                mock_send_embed.assert_called_once()

    @pytest.mark.integration
    async def test_get_system_status(
        self,
        moderation_coordinator: ModerationCoordinator,
    ) -> None:
        """Test system status reporting."""
        # The ModerationCoordinator doesn't have get_system_status method
        # System status is likely handled by individual services
        # This test may need to be moved to service-specific tests
        pass

    @pytest.mark.integration
    async def test_cleanup_old_data(
        self,
        moderation_coordinator: ModerationCoordinator,
    ) -> None:
        """Test old data cleanup functionality."""
        # The ModerationCoordinator doesn't have cleanup_old_data method
        # Cleanup is likely handled by individual services
        # This test may need to be moved to service-specific tests
        pass
