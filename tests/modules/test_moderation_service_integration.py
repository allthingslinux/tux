"""ModerationService integration tests.

Full-workflow tests for ModerationCoordinator and Cases: action execution,
mixins integration, DB integration, mod-log handling, and error paths.
"""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands
from sqlmodel import select

from tux.core.bot import Tux
from tux.core.flags import CaseModifyFlags
from tux.database.controllers import DatabaseCoordinator
from tux.database.models import Case, CaseType
from tux.database.models import CaseType as DBCaseType
from tux.database.models import Guild as GuildModel
from tux.database.service import DatabaseService
from tux.modules.moderation.cases import Cases
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


class TestModerationCoordinatorIntegration:
    """ModerationCoordinator integration with case, communication, execution services."""

    @pytest.fixture
    def mock_bot(self) -> Tux:
        """Create a mock Discord bot."""
        bot = cast(Tux, MagicMock(spec=Tux))
        bot.emoji_manager = MagicMock()
        bot.emoji_manager.get = lambda x: f":{x}:"
        return bot

    @pytest.fixture
    async def case_service(self, db_service: DatabaseService) -> CaseService:
        """Create a CaseService instance with real database."""
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
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = cast(commands.Context[Tux], MagicMock(spec=commands.Context))
        guild = cast(discord.Guild, MagicMock(spec=discord.Guild))
        guild.id = 123456789
        ctx.guild = guild
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.author.name = "Moderator"
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def mock_member(self) -> discord.Member:
        """Create a mock Discord member."""
        member = cast(discord.Member, MagicMock(spec=discord.Member))
        member.id = 555666777
        member.name = "TargetUser"
        member.top_role = MagicMock(spec=discord.Role)
        member.top_role.position = 5
        return member

    @pytest.mark.database
    @pytest.mark.integration
    async def test_complete_ban_workflow_success(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        db_service: DatabaseService,
    ) -> None:
        """Ban workflow creates case in DB, runs action, sends DM and response."""
        # Arrange
        guild = require_guild(mock_ctx)
        async with db_service.session() as session:
            guild_record = GuildModel(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Integration test ban",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert - case in DB, action run, DM and response sent
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.case_type == DBCaseType.BAN
                    assert case.case_user_id == mock_member.id
                    assert case.case_moderator_id == mock_ctx.author.id
                    assert case.case_reason == "Integration test ban"
                    assert case.guild_id == guild.id
                    assert case.case_status is True
                mock_ban_action.assert_called_once()
                mock_send_dm.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_ban_workflow_with_dm_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        db_service: DatabaseService,
    ) -> None:
        """DM failure does not prevent case creation, action execution, or moderator response."""
        # Arrange
        guild = require_guild(mock_ctx)
        async with db_service.session() as session:
            guild_record = GuildModel(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="DM failure test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert - case created, action run, response sent despite DM failure
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.case_type == DBCaseType.BAN
                    assert case.case_user_id == mock_member.id
                    assert case.case_reason == "DM failure test"
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_non_removal_action_workflow(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Warn workflow runs action, sends DM and response."""
        # Arrange
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_warn_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.id = 44
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.WARN,
                    user=mock_member,
                    reason="Integration test warning",
                    silent=False,
                    dm_action="warned",
                    actions=[(mock_warn_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_warn_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_silent_mode_workflow(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Silent mode runs action and response; send_dm is called but returns False."""
        # Arrange
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_ban_action = AsyncMock(return_value=None)
        mock_case = MagicMock()
        mock_case.id = 45
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

        with patch.object(
            moderation_coordinator._communication,
            "send_dm",
            new_callable=AsyncMock,
        ) as mock_send_dm:
            mock_send_dm.return_value = False
            with patch.object(
                moderation_coordinator,
                "_send_response_embed",
                new_callable=AsyncMock,
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.KICK,
                    user=mock_member,
                    reason="Silent mode test",
                    silent=True,
                    dm_action="kicked",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_database_failure_after_successful_action(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """DB failure after Discord action does not crash; action runs, moderator gets response."""
        # Arrange
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        moderation_coordinator._case_service.create_case = AsyncMock(
            side_effect=Exception("Database connection lost"),
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Database failure test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert - no crash, action run, response sent
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_action_execution_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        db_service: DatabaseService,
    ) -> None:
        """Discord action failure: no case or voided case, action attempted, returns None."""
        # Arrange
        guild = require_guild(mock_ctx)
        async with db_service.session() as session:
            guild_record = GuildModel(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_ban_action = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "Missing permissions"),
        )

        with patch.object(
            moderation_coordinator,
            "_send_response_embed",
            new_callable=AsyncMock,
        ):
            # Act
            result = await moderation_coordinator.execute_moderation_action(
                ctx=mock_ctx,
                case_type=DBCaseType.BAN,
                user=mock_member,
                reason="Action failure test",
                actions=[(mock_ban_action, type(None))],
            )

            # Assert
            mock_ban_action.assert_called_once()
            assert result is None
            async with db_service.session() as session:
                cases = (await session.execute(select(Case))).scalars().all()
                for case in cases:
                    assert case.case_status is False
                    assert (
                        "Discord action failed" in case.case_reason
                        or "missing permissions" in case.case_reason.lower()
                    )

    @pytest.mark.integration
    async def test_multiple_actions_execution(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Multiple actions run in sequence; all are executed."""
        # Arrange
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
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
            mock_embed_obj.description = None
            mock_embed.return_value = mock_embed_obj

            # Act
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

            # Assert
            action1.assert_called_once()
            action2.assert_called_once()
            action3.assert_called_once()

    @pytest.mark.integration
    async def test_workflow_with_duration_and_expires_at(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Workflow with expires_at passes it to create_case and sends response."""
        # Arrange
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
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
            mock_embed_obj.description = None
            mock_embed.return_value = mock_embed_obj

            # Act
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

            # Assert
            call_args = moderation_coordinator._case_service.create_case.call_args
            assert call_args[1]["case_expires_at"] == expires_at
            mock_send_embed.assert_called_once()

    @pytest.mark.database
    @pytest.mark.integration
    async def test_complete_workflow_with_mod_logging_success(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
        db_service: DatabaseService,
    ) -> None:
        """Mod-log workflow: case in DB, mod log sent, mod_log_message_id stored, DM and response."""
        # Arrange
        guild = require_guild(mock_ctx)
        async with db_service.session() as session:
            guild_record = GuildModel(id=guild.id, case_count=0)
            session.add(guild_record)
            await session.commit()
        mock_bot.db = DatabaseCoordinator(db_service)
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 123456789),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.name = "mod-log"
        mod_channel.id = 123456789
        mod_message = MagicMock()
        mod_message.id = 999888777
        mod_channel.send = AsyncMock(return_value=mod_message)
        cast(discord.Guild, mock_ctx.guild).get_channel.return_value = mod_channel
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()

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
                ) as mock_send_response,
                patch(
                    "tux.services.moderation.moderation_coordinator.EmbedCreator",
                    autospec=True,
                ) as mock_embed_creator,
            ):
                mock_embed = MagicMock()
                mock_embed_creator.create_embed.return_value = mock_embed

                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Audit log integration test",
                    silent=False,
                    dm_action="banned",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                async with db_service.session() as session:
                    cases = (await session.execute(select(Case))).scalars().all()
                    assert len(cases) == 1
                    case = cases[0]
                    assert case.case_type == DBCaseType.BAN
                    assert case.case_user_id == mock_member.id
                    assert case.case_reason == "Audit log integration test"
                    assert case.mod_log_message_id == mod_message.id
                mod_channel.send.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_dm.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_channel_not_configured(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
    ) -> None:
        """Workflow succeeds when mod log channel not configured; DM, action, response sent."""
        # Arrange
        mock_bot.db = MagicMock(spec=DatabaseCoordinator)
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, None),
        )
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_case = MagicMock()
        mock_case.id = 49
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="No mod log configured test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_channel_not_found(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
    ) -> None:
        """Mod log channel in config but missing in guild: workflow succeeds, DM/action/response sent."""
        # Arrange
        mock_bot.db = MagicMock(spec=DatabaseCoordinator)
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 123456789),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel.return_value = None
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_case = MagicMock()
        mock_case.id = 50
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Audit log channel not found test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_channel_wrong_type(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
    ) -> None:
        """Mod log channel is voice not text: workflow succeeds, DM/action/response sent."""
        # Arrange
        mock_bot.db = MagicMock(spec=DatabaseCoordinator)
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 123456789),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel = MagicMock()
        voice_channel = MagicMock(spec=discord.VoiceChannel)
        cast(discord.Guild, mock_ctx.guild).get_channel.return_value = voice_channel
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_case = MagicMock()
        mock_case.id = 51
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Wrong channel type test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_send_failure_permissions(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
    ) -> None:
        """Mod log send Forbidden: workflow succeeds, mod log attempted, DM/action/response sent."""
        # Arrange
        mock_bot.db = MagicMock(spec=DatabaseCoordinator)
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 123456789),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.name = "mod-log"
        mod_channel.id = 123456789
        mod_channel.send = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "Missing permissions"),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel.return_value = mod_channel
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_case = MagicMock()
        mock_case.id = 52
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Audit log permissions failure test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()
                mod_channel.send.assert_called_once()

    @pytest.mark.integration
    async def test_mod_log_case_update_failure(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
    ) -> None:
        """Mod log sent but case update fails: workflow succeeds, DM/action/response sent."""
        # Arrange
        mock_bot.db = MagicMock(spec=DatabaseCoordinator)
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 123456789),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.name = "mod-log"
        mod_channel.id = 123456789
        mod_message = MagicMock()
        mod_message.id = 987654321
        mod_channel.send = AsyncMock(return_value=mod_message)
        cast(discord.Guild, mock_ctx.guild).get_channel.return_value = mod_channel
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        mock_case = MagicMock()
        mock_case.id = 53
        mock_case.created_at = datetime.now(UTC)
        moderation_coordinator._case_service.create_case = AsyncMock(
            return_value=mock_case,
        )
        moderation_coordinator._case_service.update_mod_log_message_id = AsyncMock(
            side_effect=Exception("Database update failed"),
        )

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
                ) as mock_send_response,
                patch(
                    "tux.services.moderation.moderation_coordinator.EmbedCreator",
                    autospec=True,
                ) as mock_embed_creator,
            ):
                mock_embed = MagicMock()
                mock_embed_creator.create_embed.return_value = mock_embed

                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Case update failure test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_send_dm.assert_called_once()
                mock_ban_action.assert_called_once()
                mock_send_response.assert_called_once()
                mod_channel.send.assert_called_once()

    @pytest.mark.integration
    async def test_case_creation_failure_skips_mod_log(
        self,
        moderation_coordinator: ModerationCoordinator,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
        mock_bot: Tux,
    ) -> None:
        """Case creation failure: action run, DM and response sent; mod log not attempted."""
        # Arrange
        mock_bot.db = MagicMock(spec=DatabaseCoordinator)
        mock_bot.db.guild_config = MagicMock()
        mock_bot.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 123456789),
        )
        cast(discord.Guild, mock_ctx.guild).get_channel = MagicMock()
        mod_channel = MagicMock(spec=discord.TextChannel)
        mod_channel.send = AsyncMock(return_value=MagicMock())
        cast(discord.Guild, mock_ctx.guild).get_channel.return_value = mod_channel
        cast(discord.Guild, mock_ctx.guild).get_member.return_value = MagicMock()
        moderation_coordinator._case_service.create_case = AsyncMock(
            side_effect=Exception("Database error"),
        )

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
            ) as mock_send_response:
                # Act
                await moderation_coordinator.execute_moderation_action(
                    ctx=mock_ctx,
                    case_type=DBCaseType.BAN,
                    user=mock_member,
                    reason="Case creation failure test",
                    actions=[(mock_ban_action, type(None))],
                )

                # Assert
                mock_ban_action.assert_called_once()
                mock_send_dm.assert_called_once()
                mock_send_response.assert_called_once()
                mod_channel.send.assert_not_called()


class TestCaseModificationAuditLogging:
    """Mod log updates when cases are modified via Cases cog."""

    @pytest.fixture
    def mock_bot_with_db(self) -> Tux:
        """Create a mock bot with database mock."""
        bot = cast(Tux, MagicMock(spec=Tux))
        bot.emoji_manager = MagicMock()
        bot.emoji_manager.get = lambda x: f":{x}:"
        bot.db = MagicMock()
        bot.db.guild_config = MagicMock()
        bot.db.case = MagicMock()
        return bot

    @pytest.fixture
    def mock_ctx_with_guild(self) -> commands.Context[Tux]:
        """Create a mock context with guild."""
        ctx = cast(commands.Context[Tux], MagicMock(spec=commands.Context))
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
        mock_bot_with_db: Tux,
        mock_ctx_with_guild: commands.Context[Tux],
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
        mock_bot_with_db.db.guild_config.get_log_channel_ids = AsyncMock(
            return_value=(None, 111222333),
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

        guild = require_guild(mock_ctx_with_guild)
        guild.get_channel = MagicMock(return_value=mod_channel)

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
            patch(
                "tux.modules.moderation.cases.EmbedCreator",
                autospec=True,
            ) as mock_embed_creator,
            patch(
                "tux.core.decorators.get_permission_system",
                autospec=True,
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

            # Verify observable behavior:
            # 1. Case in database was updated with new reason and status
            # (Note: This test uses mocks, so we verify the update was called with correct params)
            # In a real test, we'd check the database state directly
            mock_bot_with_db.db.case.update_case_by_number.assert_called_once_with(
                123456789,
                456,
                case_reason="Updated reason",
                case_status=False,
            )

            # 2. Mod log message was fetched and edited (observable behavior)
            mod_channel.fetch_message.assert_called_once_with(999888777)
            mod_message.edit.assert_called_once()

            # 3. User received updated case embed
            mock_send_case_embed.assert_called_once()

    @pytest.mark.integration
    async def test_case_modify_no_mod_log_message_id(
        self,
        mock_bot_with_db: Tux,
        mock_ctx_with_guild: commands.Context[Tux],
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
                autospec=True,
            ) as mock_get_permission_system,
        ):
            mock_resolve_user.return_value = mock_user
            mock_permission_system = MagicMock()
            mock_permission_system.get_command_permission = AsyncMock(
                return_value=MagicMock(required_rank=0),
            )
            mock_permission_system.get_user_permission_rank = AsyncMock(
                return_value=7,
            )
            mock_get_permission_system.return_value = mock_permission_system

            flags = MagicMock(spec=CaseModifyFlags)
            flags.reason = "Updated reason"
            flags.status = None

            # Act
            await cases_cog._update_case(mock_ctx_with_guild, mock_case, flags)

            # Assert
            mock_bot_with_db.db.case.update_case_by_number.assert_called_once()
            mock_send_case_embed.assert_called_once()
