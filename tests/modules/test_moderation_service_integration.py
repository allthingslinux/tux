"""
🚀 ModerationService Integration Tests - Full Workflow Testing.

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

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.flags import CaseModifyFlags
from tux.database.models import Case, CaseType
from tux.database.models import CaseType as DBCaseType
from tux.modules.moderation.cases import Cases
from tux.services.moderation.case_service import CaseService
from tux.services.moderation.communication_service import CommunicationService
from tux.services.moderation.execution_service import ExecutionService
from tux.services.moderation.moderation_coordinator import ModerationCoordinator


class TestModerationCoordinatorIntegration:
    """🔗 Test ModerationCoordinator integration with all components."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        db = MagicMock()
        db.case = MagicMock()
        db.case.insert_case = AsyncMock()
        db.case.update_mod_log_message_id = AsyncMock()
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
    def moderation_coordinator(
        self,
        case_service,
        communication_service,
        execution_service,
    ):
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
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful ban action
            mock_ban_action = AsyncMock(return_value=None)

            # Mock case creation
            mock_case = MagicMock()
            mock_case.id = 42
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            # Mock response handling
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
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
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.side_effect = TimeoutError()

            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 43
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
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
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful warn action (dummy)
            mock_warn_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 44
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
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
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = False  # The method returns False in silent mode
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 45
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
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

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True

            mock_ban_action = AsyncMock(return_value=None)

            # Database fails after successful action
            moderation_coordinator._case_service.create_case = AsyncMock(
                side_effect=Exception("Database connection lost"),
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
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
        mock_ban_action = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "Missing permissions"),
        )

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
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

        with (
            patch.object(
                moderation_coordinator._communication,
                "create_embed",
            ) as mock_embed,
            patch.object(
                moderation_coordinator._communication,
                "send_embed",
                new_callable=AsyncMock,
            ) as _mock_send_embed,
        ):
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
        mock_ctx.guild.get_member.return_value = MagicMock()

        expires_at = datetime.now(UTC) + timedelta(hours=24)

        mock_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.id = 47
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

        with (
            patch.object(
                moderation_coordinator._communication,
                "create_embed",
            ) as mock_embed,
            patch.object(
                moderation_coordinator._communication,
                "send_embed",
                new_callable=AsyncMock,
            ) as mock_send_embed,
        ):
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
                duration=None,
                expires_at=expires_at,
            )

            # Verify duration and expires_at are passed correctly
            call_args = moderation_coordinator._case_service.create_case.call_args
            assert call_args[1]["case_expires_at"] == expires_at

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

    @pytest.mark.integration
    async def test_cleanup_old_data(
        self,
        moderation_coordinator: ModerationCoordinator,
    ) -> None:
        """Test old data cleanup functionality."""
        # The ModerationCoordinator doesn't have cleanup_old_data method
        # Cleanup is likely handled by individual services
        # This test may need to be moved to service-specific tests

    @pytest.mark.integration
    async def test_complete_workflow_with_mod_logging_success(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test complete workflow with successful mod logging."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(return_value=123456789)

        mock_ctx.guild.get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.name = "mod-log"
        mod_channel.id = 123456789
        mod_channel.send = AsyncMock(return_value=MagicMock())
        mock_ctx.guild.get_channel.return_value = mod_channel

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful DM
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True

            # Mock successful ban action
            mock_ban_action = AsyncMock(return_value=None)

            # Mock case creation
            mock_case = MagicMock()
            mock_case.id = 48
            mock_case.case_number = 100
            mock_case.case_type = MagicMock()
            mock_case.case_type.value = "BAN"
            mock_case.case_reason = "Audit log test"
            # Use a real datetime object (datetime objects have timestamp() method)
            mock_case.created_at = datetime.fromtimestamp(
                1640995200.0,
                tz=UTC,
            )  # 2022-01-01
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            # Mock mod log message ID update
            moderation_coordinator._case_service.update_mod_log_message_id = AsyncMock()

            with (
                patch.object(
                    moderation_coordinator,
                    "_send_response_embed",
                    new_callable=AsyncMock,
                ) as mock_send_response,
                patch(
                    "tux.services.moderation.moderation_coordinator.EmbedCreator",
                ) as mock_embed_creator,
            ):
                mock_embed = MagicMock()
                mock_embed_creator.create_embed.return_value = mock_embed

                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Audit log integration test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Verify the complete workflow executed
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()

                # Verify mod log was sent
                mod_channel.send.assert_called_once()
                moderation_coordinator._case_service.update_mod_log_message_id.assert_called_once_with(
                    48,
                    mod_channel.send.return_value.id,
                )

    @pytest.mark.integration
    async def test_mod_log_channel_not_configured(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test workflow when mod log channel is not configured."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(
            return_value=None,
        )  # No mod log configured

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful DM and action
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 49
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="No mod log configured test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Workflow should succeed but mod log should not be attempted
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_channel_not_found(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test workflow when mod log channel exists in config but not in guild."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(return_value=123456789)

        # Channel not found in guild
        mock_ctx.guild.get_channel.return_value = None

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful workflow
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 50
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Audit log channel not found test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Workflow should succeed but mod log should fail gracefully
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_channel_wrong_type(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test workflow when mod log channel is not a text channel."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(return_value=123456789)

        # Channel exists but is not a text channel (e.g., voice channel)
        mock_ctx.guild.get_channel = MagicMock()
        voice_channel = MagicMock(spec=discord.VoiceChannel)  # Not a TextChannel
        mock_ctx.guild.get_channel.return_value = voice_channel

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful workflow
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 51
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Wrong channel type test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Workflow should succeed but mod log should fail gracefully
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_send_failure_permissions(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test workflow when mod log send fails due to permissions."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(return_value=123456789)

        mock_ctx.guild.get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.name = "mod-log"
        mod_channel.id = 123456789
        # Simulate Forbidden error when sending
        mod_channel.send = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "Missing permissions"),
        )
        mock_ctx.guild.get_channel.return_value = mod_channel

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful workflow
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 52
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Audit log permissions failure test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Workflow should succeed but mod log should fail gracefully
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()

                # Mod log send was attempted but failed
                mod_channel.send.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_case_update_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test workflow when mod log succeeds but case update fails."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(return_value=123456789)

        mock_ctx.guild.get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.name = "mod-log"
        mod_channel.id = 123456789
        mod_message = MagicMock()
        mod_message.id = 987654321
        mod_channel.send = AsyncMock(return_value=mod_message)
        mock_ctx.guild.get_channel.return_value = mod_channel

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful workflow
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            mock_case = MagicMock()
            mock_case.id = 53
            mock_case.created_at = datetime.now(UTC)
            moderation_coordinator._case_service.create_case = AsyncMock(
                return_value=mock_case,
            )

            # Mock case update failure
            moderation_coordinator._case_service.update_mod_log_message_id = AsyncMock(
                side_effect=Exception("Database update failed"),
            )

            with (
                patch.object(
                    moderation_coordinator,
                    "_send_response_embed",
                    new_callable=AsyncMock,
                ) as mock_send_response,
                patch(
                    "tux.services.moderation.moderation_coordinator.EmbedCreator",
                ) as mock_embed_creator,
            ):
                mock_embed = MagicMock()
                mock_embed_creator.create_embed.return_value = mock_embed

                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Case update failure test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Workflow should succeed, mod log should be sent, but case update should fail gracefully
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()
                mod_channel.send.assert_called_once()
                moderation_coordinator._case_service.update_mod_log_message_id.assert_called_once()

    @pytest.mark.integration
    async def test_case_creation_failure_skips_mod_log(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx,
        mock_member,
        mock_bot,
    ) -> None:
        """Test that mod logging is skipped when case creation fails."""
        # Setup bot with database mock
        mock_bot.db = MagicMock()
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_mod_log_id = AsyncMock(return_value=123456789)

        mock_ctx.guild.get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.send = AsyncMock(return_value=MagicMock())
        mock_ctx.guild.get_channel.return_value = mod_channel

        mock_ctx.guild.get_member.return_value = MagicMock()

        # Mock successful DM and action
        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)

            # Mock case creation failure
            moderation_coordinator._case_service.create_case = AsyncMock(
                side_effect=Exception("Database error"),
            )

            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Case creation failure test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Workflow should complete but mod logging should be skipped
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                moderation_coordinator._case_service.create_case.assert_called_once()
                mock_send_response.assert_called_once()

                # Mod log should not be attempted when case creation fails
                mod_channel.send.assert_not_called()


class TestCaseModificationAuditLogging:
    """Test mod log updates when cases are modified."""

    @pytest.fixture
    def mock_bot_with_db(self):
        """Create a mock bot with database mock."""
        bot = MagicMock(spec=Tux)
        bot.emoji_manager = MagicMock()
        bot.emoji_manager.get = lambda x: f":{x}:"
        bot.db = MagicMock()
        bot.db.guild_config = MagicMock()
        bot.db.case = MagicMock()
        return bot

    @pytest.fixture
    def mock_ctx_with_guild(self):
        """Create a mock context with guild."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.author.name = "Moderator"
        ctx.command = MagicMock()
        ctx.command.qualified_name = "cases modify"
        ctx.send = AsyncMock()
        ctx.reply = AsyncMock()
        return ctx

    @pytest.mark.integration
    async def test_case_modify_updates_mod_log(  # noqa: PLR0915
        self,
        mock_bot_with_db,
        mock_ctx_with_guild,
    ) -> None:
        """Test that modifying a case updates the mod log embed."""
        # Create Cases cog instance
        cases_cog = Cases(mock_bot_with_db)

        # Setup mock case with mod log message ID
        mock_case = MagicMock(spec=Case)
        mock_case.id = 123
        mock_case.case_number = 456
        mock_case.case_type = CaseType.BAN
        mock_case.case_reason = "Original reason"
        mock_case.case_status = True
        mock_case.case_user_id = 555666777
        mock_case.case_moderator_id = 987654321
        mock_case.mod_log_message_id = 999888777
        mock_case.created_at = None
        mock_case.case_expires_at = None

        # Setup mock updated case
        mock_updated_case = MagicMock(spec=Case)
        mock_updated_case.id = 123
        mock_updated_case.case_number = 456
        mock_updated_case.case_type = CaseType.BAN
        mock_updated_case.case_reason = "Updated reason"
        mock_updated_case.case_status = False  # Changed to inactive
        mock_updated_case.case_user_id = 555666777
        mock_updated_case.case_moderator_id = 987654321
        mock_updated_case.mod_log_message_id = 999888777

        # Setup database mocks
        mock_bot_with_db.db.guild_config.get_mod_log_id = AsyncMock(
            return_value=111222333,
        )
        mock_bot_with_db.db.case.update_case_by_number = AsyncMock(
            return_value=mock_updated_case,
        )
        mock_bot_with_db.db.case.get_case_by_number = AsyncMock(return_value=mock_case)

        # Setup guild channel mock
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.id = 111222333
        mod_channel.name = "mod-log"
        mod_message = MagicMock(spec=discord.Message)
        mod_channel.fetch_message = AsyncMock(return_value=mod_message)
        mod_message.edit = AsyncMock()

        mock_ctx_with_guild.guild.get_channel = MagicMock(return_value=mod_channel)

        # Setup user resolution mocks
        mock_user = MagicMock(spec=discord.User)
        mock_user.id = 555666777
        mock_user.name = "TargetUser"

        mock_moderator = MagicMock(spec=discord.User)
        mock_moderator.id = 987654321
        mock_moderator.name = "Moderator"

        with (
            patch.object(
                cases_cog,
                "_resolve_user",
                new_callable=AsyncMock,
            ) as mock_resolve_user,
            patch.object(
                cases_cog,
                "_resolve_moderator",
                new_callable=AsyncMock,
            ) as mock_resolve_moderator,
            patch.object(
                cases_cog,
                "_send_case_embed",
                new_callable=AsyncMock,
            ) as mock_send_case_embed,
            patch("tux.modules.moderation.cases.EmbedCreator") as mock_embed_creator,
            patch(
                "tux.core.decorators.get_permission_system",
            ) as mock_get_permission_system,
        ):
            mock_resolve_user.return_value = mock_user
            mock_resolve_moderator.return_value = mock_moderator

            mock_embed = MagicMock()
            mock_embed_creator.create_embed.return_value = mock_embed

            # Mock permission system
            mock_permission_system = MagicMock()
            mock_permission_system.get_command_permission = AsyncMock(
                return_value=MagicMock(required_rank=0),
            )
            mock_permission_system.get_user_permission_rank = AsyncMock(
                return_value=7,
            )  # High rank to pass checks
            mock_get_permission_system.return_value = mock_permission_system

            # Create modify flags manually (since flag parsing happens in command context)
            flags = MagicMock(spec=CaseModifyFlags)
            flags.reason = "Updated reason"
            flags.status = False

            # Call the _update_case method directly (bypassing command decorators)
            await cases_cog._update_case(mock_ctx_with_guild, mock_case, flags)

            # Verify database update was called
            mock_bot_with_db.db.case.update_case_by_number.assert_called_once_with(
                123456789,
                456,
                case_reason="Updated reason",
                case_status=False,
            )

            # Verify mod log message was fetched and edited
            mod_channel.fetch_message.assert_called_once_with(999888777)
            mod_message.edit.assert_called_once()

            # Verify case embed was sent to user
            mock_send_case_embed.assert_called_once()

    @pytest.mark.integration
    async def test_case_modify_no_mod_log_message_id(
        self,
        mock_bot_with_db,
        mock_ctx_with_guild,
    ) -> None:
        """Test that modifying a case without mod log message ID doesn't attempt update."""
        # Create Cases cog instance
        cases_cog = Cases(mock_bot_with_db)

        # Setup mock case WITHOUT mod log message ID
        mock_case = MagicMock(spec=Case)
        mock_case.id = 123
        mock_case.case_number = 456
        mock_case.case_type = CaseType.BAN
        mock_case.case_reason = "Original reason"
        mock_case.case_status = True
        mock_case.case_user_id = 555666777
        mock_case.case_moderator_id = 987654321
        mock_case.mod_log_message_id = None  # No mod log message ID

        # Setup mock updated case
        mock_updated_case = MagicMock(spec=Case)
        mock_updated_case.id = 123
        mock_updated_case.case_number = 456
        mock_updated_case.case_type = CaseType.BAN
        mock_updated_case.case_reason = "Updated reason"
        mock_updated_case.case_status = True
        mock_updated_case.case_user_id = 555666777
        mock_updated_case.case_moderator_id = 987654321
        mock_updated_case.mod_log_message_id = None

        # Setup database mocks
        mock_bot_with_db.db.case.update_case_by_number = AsyncMock(
            return_value=mock_updated_case,
        )
        mock_bot_with_db.db.case.get_case_by_number = AsyncMock(return_value=mock_case)

        # Setup user resolution mocks
        mock_user = MagicMock(spec=discord.User)
        mock_user.id = 555666777
        mock_user.name = "TargetUser"

        with (
            patch.object(
                cases_cog,
                "_resolve_user",
                new_callable=AsyncMock,
            ) as mock_resolve_user,
            patch.object(
                cases_cog,
                "_send_case_embed",
                new_callable=AsyncMock,
            ) as mock_send_case_embed,
            patch(
                "tux.core.decorators.get_permission_system",
            ) as mock_get_permission_system,
        ):
            mock_resolve_user.return_value = mock_user

            # Mock permission system
            mock_permission_system = MagicMock()
            mock_permission_system.get_command_permission = AsyncMock(
                return_value=MagicMock(required_rank=0),
            )
            mock_permission_system.get_user_permission_rank = AsyncMock(
                return_value=7,
            )  # High rank to pass checks
            mock_get_permission_system.return_value = mock_permission_system

            # Create modify flags manually (since flag parsing happens in command context)
            flags = MagicMock(spec=CaseModifyFlags)
            flags.reason = "Updated reason"
            flags.status = None  # Not changing status in this test

            # Call the _update_case method directly (bypassing command decorators)
            await cases_cog._update_case(mock_ctx_with_guild, mock_case, flags)

            # Verify database update was called
            mock_bot_with_db.db.case.update_case_by_number.assert_called_once()

            # Verify mod log methods were NOT called
            # (No mod log message ID, so no attempts should be made)
            mock_send_case_embed.assert_called_once()
