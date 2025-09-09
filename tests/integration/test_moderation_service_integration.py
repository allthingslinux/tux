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

from tux.services.moderation.moderation_service import ModerationService
from tux.database.models import CaseType as DBCaseType
from tux.core.types import Tux


class TestModerationServiceIntegration:
    """🔗 Test ModerationService integration with all components."""

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
    def moderation_service(self, mock_bot, mock_db_service):
        """Create a ModerationService instance."""
        service = ModerationService(mock_bot, mock_db_service)
        return service

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
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test complete ban workflow from start to finish."""
        # Setup mocks for successful execution
        mock_ctx.guild.get_member.return_value = MagicMock()  # Bot is in guild

        # Mock successful DM
        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful ban action
            mock_ban_action = AsyncMock(return_value=None)

            # Mock case creation
            mock_case = MagicMock()
            mock_case.case_number = 42
            moderation_service.db.case.insert_case.return_value = mock_case

            # Mock response handling
            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        # Setup permission and condition checks to pass
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        await moderation_service.execute_moderation_action(
                            ctx=mock_ctx,
                            case_type=DBCaseType.BAN,
                            user=mock_member,
                            reason="Integration test ban",
                            silent=False,
                            dm_action="banned",
                            actions=[(mock_ban_action, type(None))],
                        )

                        # Verify the complete workflow executed
                        # Note: check_bot_permissions is not called since bot has admin
                        mock_conditions.assert_called_once()
                        mock_send_dm.assert_called_once()
                        mock_ban_action.assert_called_once()
                        moderation_service.db.case.insert_case.assert_called_once()
                        mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_ban_workflow_with_dm_failure(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test ban workflow when DM fails but action still succeeds."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock DM failure (timeout)
        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.side_effect = asyncio.TimeoutError()

            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.case_number = 43
            moderation_service.db.case.insert_case.return_value = mock_case

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        await moderation_service.execute_moderation_action(
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
                        moderation_service.db.case.insert_case.assert_called_once()
                        mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_ban_workflow_with_condition_failure(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test ban workflow failure due to condition validation."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
            with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                # Permissions pass, but conditions fail
                mock_perms.return_value = (True, None)
                mock_conditions.return_value = False

                await moderation_service.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Condition test",
                    actions=[],
                )

                # Should pass bot check but fail conditions
                # Note: check_bot_permissions is not called since bot has admin
                mock_conditions.assert_called_once()

    @pytest.mark.integration
    async def test_non_removal_action_workflow(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test workflow for non-removal actions (like warn)."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful DM (should be sent after action for non-removal)
        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful warn action (dummy)
            mock_warn_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.case_number = 44
            moderation_service.db.case.insert_case.return_value = mock_case

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        await moderation_service.execute_moderation_action(
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
                        moderation_service.db.case.insert_case.assert_called_once()
                        mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_silent_mode_workflow(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test workflow in silent mode (no DMs)."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock send_dm should not be called in silent mode
        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.case_number = 45
            moderation_service.db.case.insert_case.return_value = mock_case

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        await moderation_service.execute_moderation_action(
                            ctx=mock_ctx,
                            case_type=DBCaseType.KICK,
                            user=mock_member,
                            reason="Silent mode test",
                            silent=True,  # Silent mode
                            dm_action="kicked",
                            actions=[(mock_ban_action, type(None))],
                        )

                        # DM should not be sent in silent mode
                        mock_send_dm.assert_not_called()
                        mock_ban_action.assert_called_once()
                        moderation_service.db.case.insert_case.assert_called_once()
                        mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_database_failure_after_successful_action(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test handling of database failure after successful Discord action."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            mock_ban_action = AsyncMock(return_value=None)

            # Database fails after successful action
            moderation_service.db.case.insert_case.side_effect = Exception("Database connection lost")

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        # Should complete but log critical error for database failure
                        await moderation_service.execute_moderation_action(
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
                        moderation_service.db.case.insert_case.assert_called_once()
                        mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_action_execution_failure(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test handling of Discord API action failure."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Action fails with Discord error
        mock_ban_action = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "Missing permissions"))

        with patch.object(moderation_service, 'send_error_response', new_callable=AsyncMock) as mock_error:
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                    mock_perms.return_value = (True, None)
                    mock_conditions.return_value = True

                    await moderation_service.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=mock_member,
                        reason="Action failure test",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # Should handle the Discord error gracefully
                    mock_ban_action.assert_called_once()
                    mock_error.assert_called_once()

    @pytest.mark.integration
    async def test_multiple_actions_execution(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test execution of multiple actions in sequence."""
        mock_ctx.guild.get_member.return_value = MagicMock()

        # Multiple actions
        action1 = AsyncMock(return_value="result1")
        action2 = AsyncMock(return_value="result2")
        action3 = AsyncMock(return_value="result3")

        mock_case = MagicMock()
        mock_case.case_number = 46
        moderation_service.db.case.insert_case.return_value = mock_case

        with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock):
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                    mock_perms.return_value = (True, None)
                    mock_conditions.return_value = True

                    await moderation_service.execute_moderation_action(
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
                    moderation_service.db.case.insert_case.assert_called_once()

    @pytest.mark.integration
    async def test_workflow_with_duration_and_expires_at(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        mock_member,
    ):
        """Test workflow with duration and expiration parameters."""
        from datetime import datetime, UTC, timedelta

        mock_ctx.guild.get_member.return_value = MagicMock()

        expires_at = datetime.now(UTC) + timedelta(hours=24)

        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.case_number = 47
        moderation_service.db.case.insert_case.return_value = mock_case

        with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                    mock_perms.return_value = (True, None)
                    mock_conditions.return_value = True

                    await moderation_service.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.TEMPBAN,
                        user=mock_member,
                        reason="Duration test",
                        silent=True,
                        dm_action="temp banned",
                        actions=[(mock_action, type(None))],
                        duration="24h",
                        expires_at=expires_at,
                    )

                    # Verify duration and expires_at are passed correctly
                    call_args = moderation_service.db.case.insert_case.call_args
                    assert call_args[1]['case_expires_at'] == expires_at

                    mock_response.assert_called_once()
                    response_call_args = mock_response.call_args
                    # Duration is passed as positional argument (7th position)
                    assert response_call_args[0][6] == "24h"

    @pytest.mark.integration
    async def test_get_system_status(
        self,
        moderation_service: ModerationService,
    ):
        """Test system status reporting."""
        # This tests the monitoring integration
        status = await moderation_service.get_system_status()

        # Should return a dictionary with system status
        assert isinstance(status, dict)
        assert 'health' in status
        assert 'performance' in status
        assert 'errors' in status
        assert 'circuit_breakers' in status
        assert 'active_queues' in status

    @pytest.mark.integration
    async def test_cleanup_old_data(
        self,
        moderation_service: ModerationService,
    ):
        """Test old data cleanup functionality."""
        # Should complete without errors
        await moderation_service.cleanup_old_data()

        # This tests the monitoring cleanup integration
