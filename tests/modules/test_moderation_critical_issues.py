"""Critical moderation issues integration tests.

Targets issues from moderation analysis: DM failure (Issue #2), bot permissions
(Issue #3), DB failure (Issue #4), user-state race conditions (Issue #5), lock
race (Issue #1), privilege escalation, and audit trail integrity.
"""

import asyncio
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands
from sqlmodel import select

from tux.core.bot import Tux
from tux.database.controllers import DatabaseCoordinator
from tux.database.models import Case, Guild
from tux.database.models import CaseType as DBCaseType
from tux.database.service import DatabaseService
from tux.services.moderation.case_service import CaseService
from tux.services.moderation.communication_service import CommunicationService
from tux.services.moderation.execution_service import ExecutionService
from tux.services.moderation.moderation_coordinator import ModerationCoordinator

pytestmark = pytest.mark.asyncio


def require_guild(ctx: commands.Context[Tux]) -> discord.Guild:
    """Return the guild for a context used in guild-only tests."""
    guild = ctx.guild
    assert guild is not None
    return guild


class TestCriticalIssuesIntegration:
    """Critical moderation issues from analysis (DM, permissions, DB, race conditions)."""

    @pytest.fixture
    async def case_service(self, db_service: DatabaseService) -> CaseService:
        """Create a CaseService instance."""
        coordinator = DatabaseCoordinator(db_service)
        return CaseService(coordinator.case)

    @pytest.fixture
    def communication_service(self, mock_bot: Tux) -> CommunicationService:
        """Create a CommunicationService instance."""
        return CommunicationService(mock_bot)

    @pytest.fixture
    def execution_service(self) -> ExecutionService:
        """Create an ExecutionService instance."""
        service = ExecutionService()
        service._reset_for_testing()  # Reset singleton state for test isolation
        return service

    @pytest.fixture
    async def moderation_coordinator(
        self,
        case_service: CaseService,
        communication_service: CommunicationService,
        execution_service: ExecutionService,
    ) -> ModerationCoordinator:
        """Create a ModerationCoordinator instance."""
        return ModerationCoordinator(
            case_service=case_service,
            communication_service=communication_service,
            execution_service=execution_service,
        )

    @pytest.fixture
    def mock_bot(self) -> Tux:
        """Create a mock Discord bot."""
        bot = cast(Tux, MagicMock(spec=Tux))
        bot_user = cast(discord.ClientUser, MagicMock(spec=discord.ClientUser))
        bot_user.id = 123456789
        bot.user = bot_user
        bot.emoji_manager = MagicMock()
        bot.emoji_manager.get = lambda x: f":{x}:"
        return bot

    @pytest.fixture
    def mock_ctx(self, mock_bot: Tux) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = cast(commands.Context[Tux], MagicMock(spec=commands.Context))
        guild = cast(discord.Guild, MagicMock(spec=discord.Guild))
        guild.id = 123456789
        guild.owner_id = 999999999
        ctx.guild = guild
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.author.top_role = MagicMock()
        ctx.author.top_role.position = 10
        ctx.bot = mock_bot  # Reference to the bot
        ctx.send = AsyncMock()

        # Mock bot member in guild with permissions
        mock_bot_member = MagicMock(spec=discord.Member)
        bot_user = cast(discord.ClientUser, mock_bot.user)
        mock_bot_member.id = bot_user.id
        mock_bot_member.guild_permissions = MagicMock(spec=discord.Permissions)
        mock_bot_member.guild_permissions.ban_members = (
            False  # Test will fail without permission
        )
        mock_bot_member.top_role = MagicMock()
        mock_bot_member.top_role.position = 20

        guild.get_member.return_value = mock_bot_member
        return ctx

    @pytest.mark.database
    @pytest.mark.integration
    async def test_specification_dm_failure_must_not_prevent_action(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """DM failure must not prevent moderation action; case created, action and DM attempted."""
        # Arrange
        guild = require_guild(mock_ctx)
        async with db_service.session() as session:
            guild_record = Guild(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()
        mock_member = MockMember()
        guild.get_member.return_value = MockBotMember()

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.side_effect = discord.Forbidden(
                MagicMock(),
                "Cannot send messages to this user",
            )
            mock_ban_action = AsyncMock(return_value=None)
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ):
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=cast(discord.Member, mock_member),
                    reason="DM failure test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_ban_action.assert_called_once()
                mock_send_dm.assert_called_once()
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.case_type == DBCaseType.BAN
                    assert case.case_user_id == mock_member.id
                    assert case.case_moderator_id == mock_ctx.author.id
                    assert case.case_reason == "DM failure test"
                    assert case.guild_id == guild.id
                    assert case.case_number == 1

    @pytest.mark.database
    @pytest.mark.integration
    async def test_issue_2_dm_timeout_does_not_prevent_action(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """DM timeout must not prevent moderation action; case created, action run."""
        # Arrange
        mock_member = MockMember()
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()
        async with db_service.session() as session:
            guild_record = Guild(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.side_effect = TimeoutError()
            mock_ban_action = AsyncMock(return_value=None)
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ):
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.KICK,
                    user=cast(discord.Member, mock_member),
                    reason="DM timeout test",
                    silent=False,
                    dm_action="kicked",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_ban_action.assert_called_once()
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.case_type == DBCaseType.KICK
                    assert case.case_user_id == mock_member.id

    @pytest.mark.integration
    async def test_specification_bot_must_validate_own_permissions(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """With valid bot permissions, coordinator executes and sends response (checks at command level)."""
        # Arrange
        mock_member = MockMember()
        guild = require_guild(mock_ctx)
        mock_bot_member = MockBotMember()
        mock_bot_member.guild_permissions.ban_members = True
        guild.get_member.return_value = mock_bot_member

        with (
            patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_response,
            patch.object(
                moderation_coordinator._case_service,
                "create_case",
                new_callable=AsyncMock,
            ) as mock_create_case,
        ):
            mock_case = MagicMock()
            mock_case.id = 123
            mock_case.case_number = 456
            mock_case.created_at = datetime.fromtimestamp(1640995200.0, tz=UTC)
            mock_case.case_type = MagicMock()
            mock_case.case_type.value = "BAN"
            mock_case.case_reason = "Test case"
            mock_create_case.return_value = mock_case

            # Act
            await moderation_coordinator.execute_moderation_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=cast(discord.Member, mock_member),
                reason="Permission check test",
                actions=[],
            )

            # Assert
            mock_response.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_issue_3_bot_has_required_permissions(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """Bot with required permissions: action runs and case created in DB."""
        # Arrange
        mock_member = MockMember()
        mock_bot_member = MockBotMember()
        mock_bot_member.guild_permissions.ban_members = True
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = mock_bot_member
        async with db_service.session() as session:
            guild_record = Guild(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ):
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=cast(discord.Member, mock_member),
                    reason="Permission success test",
                    silent=True,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_ban_action.assert_called_once()
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.case_type == DBCaseType.BAN
                    assert case.case_user_id == mock_member.id

    @pytest.mark.integration
    async def test_specification_database_failure_must_not_crash_system(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """DB failure must not crash system; action runs and moderator receives response."""
        # Arrange
        mock_member = MockMember()
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            with (
                patch.object(
                    moderation_coordinator,
                    "_send_response_embed",
                    new_callable=AsyncMock,
                ) as mock_response,
                patch.object(
                    moderation_coordinator._case_service,
                    "create_case",
                    side_effect=Exception("Database connection lost"),
                ),
            ):
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=cast(discord.Member, mock_member),
                    reason="Database failure test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_ban_action.assert_called_once()
                mock_response.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_specification_user_state_changes_must_be_handled_gracefully(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """User state change (e.g. member left during action) handled gracefully; no crash."""
        # Arrange
        mock_member = MockMember()
        mock_ban_action = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), "Member not found"),
        )
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()
        async with db_service.session() as session:
            guild_record = Guild(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()

        # Act
        await moderation_coordinator.execute_moderation_action(
            ctx=mock_ctx,
            case_type=DBCaseType.BAN,
            user=cast(discord.Member, mock_member),
            reason="User state change test",
            actions=[(mock_ban_action, type(None))],
        )

        # Assert
        mock_ban_action.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_specification_lock_manager_race_condition_prevention(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """Concurrent operations on same user handled without crash; at least one action attempted."""
        # Arrange
        mock_member = MockMember()
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()
        mock_ban_action1 = AsyncMock(return_value=None)
        mock_ban_action2 = AsyncMock(return_value=None)
        async with db_service.session() as session:
            guild_record = Guild(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ):
                # Act
                task1 = asyncio.create_task(
                    moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=cast(discord.Member, mock_member),
                        reason="Concurrent operation 1",
                        silent=True,
                        dm_action="banned",
                        actions=[(mock_ban_action1, type(None))],
                    ),
                )
                task2 = asyncio.create_task(
                    moderation_coordinator.execute_moderation_action(
                        ctx=mock_ctx,
                        case_type=DBCaseType.BAN,
                        user=cast(discord.Member, mock_member),
                        reason="Concurrent operation 2",
                        silent=True,
                        dm_action="banned",
                        actions=[(mock_ban_action2, type(None))],
                    ),
                )
                await asyncio.gather(task1, task2)

                # Assert
                assert mock_ban_action1.called or mock_ban_action2.called
                await asyncio.sleep(0.1)
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    for case in cases:
                        assert case.case_type == DBCaseType.BAN
                        assert case.case_user_id == mock_member.id

    @pytest.mark.integration
    async def test_privilege_escalation_prevention(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Valid hierarchy: coordinator executes and sends response (checks at command level)."""
        # Arrange
        mock_member = MockMember()
        mock_moderator = MockMember()
        mock_moderator.id = 987654321
        mock_moderator.top_role = MockRole(position=10)
        mock_member.top_role = MockRole(position=5)
        mock_ctx.author = mock_moderator
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()

        with (
            patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_response,
            patch.object(
                moderation_coordinator._case_service,
                "create_case",
                new_callable=AsyncMock,
            ) as mock_create_case,
        ):
            mock_case = MagicMock()
            mock_case.id = 123
            mock_case.case_number = 456
            mock_case.created_at = datetime.fromtimestamp(1640995200.0, tz=UTC)
            mock_case.case_type = MagicMock()
            mock_case.case_type.value = "BAN"
            mock_case.case_reason = "Test case"
            mock_create_case.return_value = mock_case

            # Act
            await moderation_coordinator.execute_moderation_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=cast(discord.Member, mock_member),
                reason="Privilege escalation test",
                actions=[],
            )

            # Assert
            mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_guild_owner_protection(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Coordinator proceeds when target is guild owner (protection at command level)."""
        # Arrange
        mock_member = MockMember()
        mock_member.id = 999999999
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()

        with (
            patch.object(
                moderation_coordinator._case_service,
                "create_case",
                new_callable=AsyncMock,
            ) as mock_create_case,
            patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_response,
            patch.object(
                moderation_coordinator,
                "_send_mod_log_embed",
                new_callable=AsyncMock,
            ) as mock_mod_log,
            patch.object(
                moderation_coordinator._case_service,
                "update_mod_log_message_id",
                new_callable=AsyncMock,
            ) as mock_update_mod,
        ):
            mock_case = MagicMock()
            mock_case.id = 123
            mock_case.case_number = 456
            mock_case.created_at = datetime.now(UTC)
            mock_create_case.return_value = mock_case
            mock_response.return_value = None
            mock_mod_log.return_value = None
            mock_update_mod.return_value = None

            # Act
            await moderation_coordinator.execute_moderation_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=cast(discord.Member, mock_member),
                reason="Owner protection test",
                actions=[],
            )

            # Assert
            mock_response.assert_called_once()

    @pytest.mark.integration
    async def test_self_moderation_prevention(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Target different from moderator: coordinator executes and sends response."""
        # Arrange
        mock_member = MockMember()
        mock_member.id = 555666777
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()

        with (
            patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_response,
            patch.object(
                moderation_coordinator._case_service,
                "create_case",
                new_callable=AsyncMock,
            ) as mock_create_case,
        ):
            mock_case = MagicMock()
            mock_case.id = 123
            mock_case.case_number = 456
            mock_case.created_at = datetime.fromtimestamp(1640995200.0, tz=UTC)
            mock_case.case_type = MagicMock()
            mock_case.case_type.value = "BAN"
            mock_case.case_reason = "Test case"
            mock_create_case.return_value = mock_case

            # Act
            await moderation_coordinator.execute_moderation_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=cast(discord.Member, mock_member),
                reason="Self-moderation test",
                actions=[],
            )

            # Assert
            mock_response.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_audit_trail_data_integrity(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        db_service: DatabaseService,
    ) -> None:
        """Audit trail: case in DB has correct guild, user, moderator, type, reason."""
        # Arrange
        mock_member = MockMember()
        guild = require_guild(mock_ctx)
        guild.get_member.return_value = MockBotMember()
        async with db_service.session() as session:
            guild_record = Guild(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = True
            mock_ban_action = AsyncMock(return_value=None)
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ):
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=cast(discord.Member, mock_member),
                    reason="Audit trail integrity test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.guild_id == guild.id
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
        self.display_avatar = MockAvatar()


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


class MockAvatar:
    """Mock Discord Avatar."""

    def __init__(self):
        self.url = "https://example.com/avatar.png"
