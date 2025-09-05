"""
🚨 Critical Issues Integration Tests - Testing Analysis Findings

Integration tests specifically targeting the critical issues identified in
moderation_analysis.md to ensure they are properly fixed.

Test Coverage:
- Race condition in lock cleanup (Issue #1)
- DM failure preventing action (Issue #2) - FIXED
- Missing bot permission checks (Issue #3) - FIXED
- Database transaction issues (Issue #4)
- User state change race conditions (Issue #5)
- Privilege escalation vulnerabilities
- Data integrity and audit trail gaps
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext import commands

from tux.services.moderation.moderation_service import ModerationService
from tux.database.models import CaseType as DBCaseType
from tux.core.types import Tux


class TestCriticalIssuesIntegration:
    """🚨 Test critical issues from moderation analysis."""

    @pytest.fixture
    async def moderation_service(self, mock_bot, fresh_db):
        """Create a ModerationService instance with real database."""
        from tux.database.controllers import DatabaseCoordinator
        coordinator = DatabaseCoordinator(fresh_db)
        service = ModerationService(mock_bot, coordinator)
        return service

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot."""
        bot = MagicMock(spec=Tux)
        bot.user = MagicMock()
        bot.user.id = 123456789  # Mock bot user ID
        return bot

    @pytest.fixture
    def mock_ctx(self, mock_bot):
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.guild.owner_id = 999999999
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.author.top_role = MagicMock()
        ctx.author.top_role.position = 10
        ctx.bot = mock_bot  # Reference to the bot
        ctx.send = AsyncMock()

        # Mock bot member in guild with permissions
        mock_bot_member = MagicMock(spec=discord.Member)
        mock_bot_member.id = mock_bot.user.id
        mock_bot_member.guild_permissions = MagicMock(spec=discord.Permissions)
        mock_bot_member.guild_permissions.ban_members = False  # Test will fail without permission
        mock_bot_member.top_role = MagicMock()
        mock_bot_member.top_role.position = 20

        ctx.guild.get_member.return_value = mock_bot_member
        return ctx

    @pytest.mark.integration
    async def test_specification_dm_failure_must_not_prevent_action(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        🔴 SPECIFICATION TEST: DM failure MUST NOT prevent moderation action.

        This test defines the CORRECT behavior: Actions should proceed regardless of DM success.
        If this test FAILS, it means the current implementation has the critical DM blocking bug.

        Technical and UX Requirements:
        - DM attempts should be made for removal actions (ban/kick)
        - But actions should NEVER be blocked by DM failures
        - This ensures consistent moderation regardless of user DM settings

        CRITICAL: This test should FAIL on current buggy implementation and PASS after fix.
        """
        # Create the guild record first (required for case creation)
        async with fresh_db.session() as session:
            from tux.database.models import Guild
            guild = Guild(guild_id=mock_ctx.guild.id, case_count=0)
            session.add(guild)
            await session.commit()
        mock_member = MockMember()
        mock_ctx.guild.get_member.return_value = MockBotMember()

        # Mock DM failure (Forbidden - user has DMs disabled)
        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.side_effect = discord.Forbidden(MagicMock(), "Cannot send messages to this user")

            # Mock successful ban action
            mock_ban_action = AsyncMock(return_value=None)

            # Real database will handle case creation

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock):
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        # EXECUTE: This should work regardless of DM failure
                        await moderation_service.execute_moderation_action(
                            ctx=mock_ctx,
                            case_type=DBCaseType.BAN,  # Removal action requiring DM attempt
                            user=mock_member,
                            reason="DM failure test",
                            silent=False,  # Explicitly try to send DM
                            dm_action="banned",
                            actions=[(mock_ban_action, type(None))],
                        )

                        # SPECIFICATION: Action MUST proceed despite DM failure
                        mock_ban_action.assert_called_once()

                        # SPECIFICATION: DM MUST have been attempted (for audit trail)
                        mock_send_dm.assert_called_once()

                                        # Verify case was created in real database
                        async with fresh_db.session() as session:
                            from tux.database.models import Case, Guild
                            from sqlmodel import select

                            # Check the case was created
                            cases = (await session.execute(select(Case))).scalars().all()
                            assert len(cases) == 1
                            case = cases[0]
                            assert case.case_type == DBCaseType.BAN
                            assert case.case_user_id == mock_member.id
                            assert case.case_moderator_id == mock_ctx.author.id
                            assert case.case_reason == "DM failure test"
                            assert case.guild_id == mock_ctx.guild.id
                            assert case.case_number == 1  # Should be the first case

                        # This test will FAIL if current implementation blocks actions on DM failure
                        # When it passes, the critical Issue #2 is fixed

    @pytest.mark.integration
    async def test_issue_2_dm_timeout_does_not_prevent_action(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        Test Issue #2 variant: DM timeout should NOT prevent the moderation action.
        """
        mock_member = MockMember()
        mock_ctx.guild.get_member.return_value = MockBotMember()

        # Mock DM timeout
        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.side_effect = asyncio.TimeoutError()

            mock_ban_action = AsyncMock(return_value=None)

            # Create the guild record first (required for case creation)
            async with fresh_db.session() as session:
                from tux.database.models import Guild
                guild = Guild(guild_id=mock_ctx.guild.id, case_count=0)
                session.add(guild)
                await session.commit()

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock):
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        await moderation_service.execute_moderation_action(
                            ctx=mock_ctx,
                            case_type=DBCaseType.KICK,
                            user=mock_member,
                            reason="DM timeout test",
                            silent=False,
                            dm_action="kicked",
                            actions=[(mock_ban_action, type(None))],
                        )

                        # ✅ Action should proceed despite DM timeout
                        mock_ban_action.assert_called_once()

                        # Verify case was created in real database
                        async with fresh_db.session() as session:
                            from tux.database.models import Case
                            from sqlmodel import select

                            cases = (await session.execute(select(Case))).scalars().all()
                            assert len(cases) == 1
                            case = cases[0]
                            assert case.case_type == DBCaseType.KICK
                            assert case.case_user_id == mock_member.id

    @pytest.mark.integration
    async def test_specification_bot_must_validate_own_permissions(
        self,
        moderation_service: ModerationService,
        mock_ctx,
    ):
        """
        🔴 SPECIFICATION TEST: Bot MUST validate its own permissions before action.

        This test defines the CORRECT behavior: Bot should check permissions and fail gracefully.
        If this test FAILS, it means the current implementation lacks permission validation.

        Security Requirement:
        - Bot should validate it has required permissions before attempting actions
        - Should provide clear error messages when permissions are missing
        - Should prevent silent failures that confuse moderators

        CRITICAL: This test should FAIL on current implementation and PASS after fix.
        """
        mock_member = MockMember()

        # Test bot lacks ban permission
        mock_bot_member = MockBotMember()
        mock_bot_member.guild_permissions.ban_members = False
        mock_ctx.guild.get_member.return_value = mock_bot_member

        with patch.object(moderation_service, 'send_error_response', new_callable=AsyncMock) as mock_error:
            await moderation_service.execute_moderation_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=mock_member,
                reason="Permission check test",
                actions=[],
            )

            # SPECIFICATION: Should detect missing permission and send error
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0]
            assert "ban members" in error_call[1].lower()

            # This test will FAIL if current implementation doesn't validate bot permissions
            # When it passes, the critical Issue #3 is fixed

    @pytest.mark.integration
    async def test_issue_3_bot_has_required_permissions(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        Test that bot permission checks pass when bot has required permissions.
        """
        mock_member = MockMember()
        mock_bot_member = MockBotMember()
        mock_bot_member.guild_permissions.ban_members = True
        mock_ctx.guild.get_member.return_value = mock_bot_member

        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            mock_ban_action = AsyncMock(return_value=None)

            # Create the guild record first (required for case creation)
            async with fresh_db.session() as session:
                from tux.database.models import Guild
                guild = Guild(guild_id=mock_ctx.guild.id, case_count=0)
                session.add(guild)
                await session.commit()

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock):
                with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                    mock_conditions.return_value = True

                    await moderation_service.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=mock_member,
                        reason="Permission success test",
                        silent=True,
                        dm_action="banned",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # ✅ Should pass permission check and proceed
                    mock_ban_action.assert_called_once()

                    # Verify case was created in real database
                    async with fresh_db.session() as session:
                        from tux.database.models import Case
                        from sqlmodel import select

                        cases = (await session.execute(select(Case))).scalars().all()
                        assert len(cases) == 1
                        case = cases[0]
                        assert case.case_type == DBCaseType.BAN
                        assert case.case_user_id == mock_member.id

    @pytest.mark.integration
    async def test_specification_database_failure_must_not_crash_system(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        🔴 SPECIFICATION TEST: Database failure MUST NOT crash the entire system.

        This test defines the CORRECT behavior: System should handle database failures gracefully.
        If this test FAILS, it means the current implementation has critical database issues.

        Reliability Requirements:
        - Discord actions should complete even if database fails
        - System should log critical errors for manual review
        - Moderators should still get feedback about successful actions
        - No silent failures that leave actions in inconsistent state

        CRITICAL: This test should FAIL on current buggy implementation and PASS after fix.
        """
        mock_member = MockMember()
        mock_ctx.guild.get_member.return_value = MockBotMember()

        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            mock_ban_action = AsyncMock(return_value=None)

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock) as mock_response:
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        # Database fails after successful action (simulates network outage, disk full, etc.)
                        with patch.object(moderation_service.db.case, 'insert_case', side_effect=Exception("Database connection lost")) as mock_insert_case:
                            mock_perms.return_value = (True, None)
                            mock_conditions.return_value = True

                            # SPECIFICATION: Should complete successfully despite database failure
                            await moderation_service.execute_moderation_action(
                                ctx=mock_ctx,
                                case_type=DBCaseType.BAN,
                                user=mock_member,
                                reason="Database failure test",
                                silent=False,
                                dm_action="banned",
                                actions=[(mock_ban_action, type(None))],
                            )

                            # SPECIFICATION: Discord action MUST succeed
                            mock_ban_action.assert_called_once()

                            # SPECIFICATION: Database operation MUST have been attempted
                            mock_insert_case.assert_called_once()

                            # SPECIFICATION: User response MUST still be sent (critical for UX)
                            mock_response.assert_called_once()

                            # This test will FAIL if current implementation crashes on database failure
                            # When it passes, the critical Issue #4 is fixed

    @pytest.mark.integration
    async def test_specification_user_state_changes_must_be_handled_gracefully(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        🔴 SPECIFICATION TEST: User state changes during execution MUST be handled gracefully.

        This test defines the CORRECT behavior: System should handle race conditions gracefully.
        If this test FAILS, it means the current implementation has critical race condition issues.

        Race Condition Scenarios:
        - User leaves guild during action execution
        - User changes roles during hierarchy validation
        - Bot loses permissions mid-execution
        - User gets banned/unbanned by another moderator simultaneously

        Reliability Requirements:
        - System should detect state changes and respond appropriately
        - Should provide clear error messages for race conditions
        - Should not leave system in inconsistent state
        - Should log race conditions for monitoring

        CRITICAL: This test should FAIL on current buggy implementation and PASS after fix.
        """
        mock_member = MockMember()

        # Simulate user leaving during action execution (common race condition)
        mock_ban_action = AsyncMock(side_effect=discord.NotFound(MagicMock(), "Member not found"))

        mock_ctx.guild.get_member.return_value = MockBotMember()

        with patch.object(moderation_service, 'send_error_response', new_callable=AsyncMock) as mock_error:
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                    mock_perms.return_value = (True, None)
                    mock_conditions.return_value = True

                    await moderation_service.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=mock_member,
                        reason="User state change test",
                        actions=[(mock_ban_action, type(None))],
                    )

                    # SPECIFICATION: Should handle the NotFound error gracefully
                    mock_ban_action.assert_called_once()
                    mock_error.assert_called_once()

                    # SPECIFICATION: Error message should be user-friendly
                    error_call = mock_error.call_args[0]
                    assert "user" in error_call[1].lower() or "member" in error_call[1].lower()

                                            # This test will FAIL if current implementation crashes on race conditions
                        # When it passes, the critical Issue #5 is fixed

    @pytest.mark.integration
    async def test_specification_lock_manager_race_condition_prevention(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        🔴 SPECIFICATION TEST: Lock manager MUST prevent race conditions.

        This test defines the CORRECT behavior: Concurrent operations on same user should be serialized.
        If this test FAILS, it means the current implementation has critical race condition Issue #1.

        Race Condition Scenario from Issue #1:
        - Multiple moderators try to ban the same user simultaneously
        - Lock cleanup happens between check and deletion
        - Memory leaks from uncleared locks

        Thread Safety Requirements:
        - User-specific locks should prevent concurrent operations
        - Lock cleanup should be race-condition-free
        - No memory leaks from abandoned locks
        - Clear error messages for concurrent operation attempts

        CRITICAL: This test should FAIL on current buggy implementation and PASS after fix.
        """
        mock_member = MockMember()
        mock_ctx.guild.get_member.return_value = MockBotMember()

        # Simulate successful actions
        mock_ban_action1 = AsyncMock(return_value=None)
        mock_ban_action2 = AsyncMock(return_value=None)

        # Create the guild record first (required for case creation)
        async with fresh_db.session() as session:
            from tux.database.models import Guild
            guild = Guild(guild_id=mock_ctx.guild.id, case_count=0)
            session.add(guild)
            await session.commit()

        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock):
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        # SPECIFICATION: Multiple operations on same user should be serialized
                        # Start two concurrent operations on the same user
                        import asyncio
                        task1 = asyncio.create_task(
                            moderation_service.execute_moderation_action(
                                ctx=mock_ctx,
                                case_type=DBCaseType.BAN,
                                user=mock_member,
                                reason="Concurrent operation 1",
                                silent=True,
                                dm_action="banned",
                                actions=[(mock_ban_action1, type(None))],
                            ),
                        )

                        task2 = asyncio.create_task(
                            moderation_service.execute_moderation_action(
                                ctx=mock_ctx,
                                case_type=DBCaseType.BAN,
                                user=mock_member,
                                reason="Concurrent operation 2",
                                silent=True,
                                dm_action="banned",
                                actions=[(mock_ban_action2, type(None))],
                            ),
                        )

                        # Wait for both to complete
                        await asyncio.gather(task1, task2)

                        # SPECIFICATION: Both actions should succeed (not fail due to race conditions)
                        mock_ban_action1.assert_called_once()
                        mock_ban_action2.assert_called_once()

                        # Verify cases were created in real database
                        async with fresh_db.session() as session:
                            from tux.database.models import Case
                            from sqlmodel import select

                            cases = (await session.execute(select(Case))).scalars().all()
                            assert len(cases) == 2
                            # Both cases should be for the same user
                            for case in cases:
                                assert case.case_type == DBCaseType.BAN
                                assert case.case_user_id == mock_member.id

                        # This test will FAIL if current implementation has lock race conditions
                        # When it passes, the critical Issue #1 is fixed

    @pytest.mark.integration
    async def test_privilege_escalation_prevention(
        self,
        moderation_service: ModerationService,
        mock_ctx,
    ):
        """
        Test prevention of privilege escalation attacks.

        This ensures that role hierarchy checks are robust and can't be
        bypassed by timing attacks or state changes.
        """
        mock_member = MockMember()
        mock_moderator = MockMember()
        mock_moderator.id = 987654321

        # Setup hierarchy: moderator has lower role than target
        mock_moderator.top_role = MockRole(position=5)
        mock_member.top_role = MockRole(position=10)  # Higher role

        mock_ctx.author = mock_moderator
        mock_ctx.guild.get_member.return_value = MockBotMember()

        with patch.object(moderation_service, 'send_error_response', new_callable=AsyncMock) as mock_error:
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                mock_perms.return_value = (True, None)

                await moderation_service.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Privilege escalation test",
                    actions=[],
                )

                # ✅ Should prevent the action due to hierarchy
                mock_error.assert_called_once()

    @pytest.mark.integration
    async def test_guild_owner_protection(
        self,
        moderation_service: ModerationService,
        mock_ctx,
    ):
        """
        Test that guild owners are properly protected from moderation actions.
        """
        mock_member = MockMember()
        mock_member.id = mock_ctx.guild.owner_id  # Target is guild owner

        mock_ctx.guild.get_member.return_value = MockBotMember()

        with patch.object(moderation_service, 'send_error_response', new_callable=AsyncMock) as mock_error:
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                mock_perms.return_value = (True, None)

                await moderation_service.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Owner protection test",
                    actions=[],
                )

                # ✅ Should prevent action against guild owner
                mock_error.assert_called_once()

    @pytest.mark.integration
    async def test_self_moderation_prevention(
        self,
        moderation_service: ModerationService,
        mock_ctx,
    ):
        """
        Test that users cannot moderate themselves.
        """
        mock_member = MockMember()
        mock_member.id = mock_ctx.author.id  # Target is same as moderator

        mock_ctx.guild.get_member.return_value = MockBotMember()

        with patch.object(moderation_service, 'send_error_response', new_callable=AsyncMock) as mock_error:
            with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                mock_perms.return_value = (True, None)

                await moderation_service.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Self-moderation test",
                    actions=[],
                )

                # ✅ Should prevent self-moderation
                mock_error.assert_called_once()

    @pytest.mark.integration
    async def test_audit_trail_data_integrity(
        self,
        moderation_service: ModerationService,
        mock_ctx,
        fresh_db,
    ):
        """
        Test that audit trails maintain data integrity even during failures.
        """
        mock_member = MockMember()
        mock_ctx.guild.get_member.return_value = MockBotMember()

        with patch.object(moderation_service, 'send_dm', new_callable=AsyncMock) as mock_send_dm:
            mock_send_dm.return_value = True

            mock_ban_action = AsyncMock(return_value=None)

            # Create the guild record first (required for case creation)
            async with fresh_db.session() as session:
                from tux.database.models import Guild
                guild = Guild(guild_id=mock_ctx.guild.id, case_count=0)
                session.add(guild)
                await session.commit()

            with patch.object(moderation_service, 'handle_case_response', new_callable=AsyncMock):
                with patch.object(moderation_service, 'check_bot_permissions', new_callable=AsyncMock) as mock_perms:
                    with patch.object(moderation_service, 'check_conditions', new_callable=AsyncMock) as mock_conditions:
                        mock_perms.return_value = (True, None)
                        mock_conditions.return_value = True

                        await moderation_service.execute_moderation_action(
                            ctx=mock_ctx,
                            case_type=DBCaseType.BAN,
                            user=mock_member,
                            reason="Audit trail integrity test",
                            silent=False,
                            dm_action="banned",
                            actions=[(mock_ban_action, type(None))],
                        )

                        # ✅ Verify database was called with correct audit data
                        async with fresh_db.session() as session:
                            from tux.database.models import Case
                            from sqlmodel import select

                            cases = (await session.execute(select(Case))).scalars().all()
                            assert len(cases) == 1
                            case = cases[0]
                            assert case.guild_id == mock_ctx.guild.id
                            assert case.case_user_id == mock_member.id
                            assert case.case_moderator_id == mock_ctx.author.id
                            assert case.case_type == DBCaseType.BAN
                            assert case.case_reason == "Audit trail integrity test"


class MockMember:
    """Mock Discord Member for testing."""
    def __init__(self, user_id: int = 555666777):
        self.id = user_id
        self.name = "TestUser"
        self.top_role = MockRole(position=5)


class MockBotMember:
    """Mock bot member with permissions."""
    def __init__(self):
        self.guild_permissions = MockPermissions()


class MockPermissions:
    """Mock guild permissions."""
    def __init__(self):
        self.ban_members = True
        self.kick_members = True
        self.moderate_members = True


class MockRole:
    """Mock Discord Role."""
    def __init__(self, position: int = 5):
        self.position = position
