"""
🚀 CaseResponseHandler Unit Tests - Case Response Creation & Sending

Tests for the CaseResponseHandler mixin that handles creating and sending
case response embeds after moderation actions.

Test Coverage:
- Case response embed creation
- Case title formatting
- Field creation for moderators and targets
- DM status indication
- Response sending coordination
- Duration handling in case titles
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands

from tux.services.moderation.case_response_handler import CaseResponseHandler
from tux.database.models import CaseType as DBCaseType
from tux.core.types import Tux


class TestCaseResponseHandler:
    """📋 Test CaseResponseHandler functionality."""

    @pytest.fixture
    def response_handler(self) -> CaseResponseHandler:
        """Create a CaseResponseHandler instance for testing."""
        return CaseResponseHandler()

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.name = "Moderator"
        ctx.author.display_avatar = MagicMock()
        ctx.author.display_avatar.url = "https://example.com/avatar.png"
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def mock_member(self) -> discord.Member:
        """Create a mock Discord member."""
        member = MagicMock(spec=discord.Member)
        member.id = 555666777
        member.name = "TargetUser"
        return member

    @pytest.mark.unit
    async def test_handle_case_response_with_case_number(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test case response handling with valid case number."""
        # Mock embed creation
        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        result = await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.BAN,
            case_number=42,
            reason="Test ban reason",
            user=mock_member,
            dm_sent=True,
            duration="1h",
        )

        assert result is not None
        response_handler.send_embed.assert_called_once()

        # Check the embed creation call
        create_call = response_handler.create_embed.call_history[0]
        assert create_call['title'] == "Case #42 (1h BAN)"
        assert create_call['color'] == 16217742  # CASE color

    @pytest.mark.unit
    async def test_handle_case_response_without_case_number(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test case response handling without case number."""
        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        result = await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.WARN,
            case_number=None,
            reason="Test warning",
            user=mock_member,
            dm_sent=False,
        )

        assert result is not None

        # Check the embed creation call
        create_call = response_handler.create_embed.call_history[0]
        assert create_call['title'] == "Case #0 (WARN)"

    @pytest.mark.unit
    async def test_handle_case_response_dm_sent_indicator(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sent status indication in case response."""
        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        # Test with DM sent
        await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.KICK,
            case_number=123,
            reason="Test kick",
            user=mock_member,
            dm_sent=True,
        )

        # Verify the embed creation was called
        create_call = response_handler.create_embed.call_history[0]
        assert create_call['title'] == "Case #123 (KICK)"

        # Reset for next test
        response_handler.create_embed.call_history.clear()

        # Test without DM sent
        await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.KICK,
            case_number=124,
            reason="Test kick no DM",
            user=mock_member,
            dm_sent=False,
        )

        create_call = response_handler.create_embed.call_history[0]
        assert create_call['title'] == "Case #124 (KICK)"

    @pytest.mark.unit
    async def test_format_case_title_with_duration(
        self,
        response_handler: CaseResponseHandler,
    ) -> None:
        """Test case title formatting with duration."""
        title = response_handler._format_case_title(DBCaseType.TIMEOUT, 123, "30m")
        assert title == "Case #123 (30m TIMEOUT)"

    @pytest.mark.unit
    async def test_format_case_title_without_duration(
        self,
        response_handler: CaseResponseHandler,
    ) -> None:
        """Test case title formatting without duration."""
        title = response_handler._format_case_title(DBCaseType.BAN, 456, None)
        assert title == "Case #456 (BAN)"

    @pytest.mark.unit
    async def test_format_case_title_zero_case_number(
        self,
        response_handler: CaseResponseHandler,
    ) -> None:
        """Test case title formatting with zero case number."""
        title = response_handler._format_case_title(DBCaseType.WARN, 0, None)
        assert title == "Case #0 (WARN)"

    @pytest.mark.unit
    async def test_format_case_title_large_case_number(
        self,
        response_handler: CaseResponseHandler,
    ) -> None:
        """Test case title formatting with large case number."""
        title = response_handler._format_case_title(DBCaseType.JAIL, 999999, "1d")
        assert title == "Case #999999 (1d JAIL)"

    @pytest.mark.unit
    async def test_handle_case_response_with_different_case_types(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test case response with different case types."""
        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        case_types = [
            DBCaseType.BAN,
            DBCaseType.KICK,
            DBCaseType.TIMEOUT,
            DBCaseType.WARN,
            DBCaseType.JAIL,
            DBCaseType.UNBAN,
            DBCaseType.UNTIMEOUT,
            DBCaseType.UNJAIL,
        ]

        for i, case_type in enumerate(case_types):
            response_handler.create_embed.call_history.clear()

            await response_handler.handle_case_response(
                ctx=mock_ctx,
                case_type=case_type,
                case_number=i + 1,
                reason=f"Test {case_type.value}",
                user=mock_member,
                dm_sent=True,
            )

            create_call = response_handler.create_embed.call_history[0]
            assert case_type.value in create_call['title']

    @pytest.mark.unit
    async def test_handle_case_response_field_creation(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test that proper fields are created for case response."""
        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.BAN,
            case_number=42,
            reason="Test ban reason",
            user=mock_member,
            dm_sent=True,
        )

        create_call = response_handler.create_embed.call_history[0]
        fields = create_call['fields']

        # Should have 3 fields: Moderator, Target, Reason
        assert len(fields) == 3

        # Check field names
        assert fields[0][0] == "Moderator"
        assert fields[1][0] == "Target"
        assert fields[2][0] == "Reason"

        # Check field inline settings
        assert fields[0][2] is True   # Moderator inline
        assert fields[1][2] is True   # Target inline
        assert fields[2][2] is False  # Reason not inline

    @pytest.mark.unit
    async def test_handle_case_response_send_embed_failure(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test handling of embed sending failure."""
        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=None)  # Failed to send

        result = await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.WARN,
            case_number=1,
            reason="Test warning",
            user=mock_member,
            dm_sent=False,
        )

        assert result is None

    @pytest.mark.unit
    async def test_handle_case_response_with_long_reason(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test case response with very long reason."""
        long_reason = "A" * 500  # Very long reason

        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.WARN,
            case_number=1,
            reason=long_reason,
            user=mock_member,
            dm_sent=True,
        )

        create_call = response_handler.create_embed.call_history[0]
        fields = create_call['fields']

        # Reason field should contain the long reason
        reason_field = next(field for field in fields if field[0] == "Reason")
        assert reason_field[1] == f"-# > {long_reason}"

    @pytest.mark.unit
    async def test_handle_case_response_with_special_characters(
        self,
        response_handler: CaseResponseHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test case response with special characters in reason."""
        special_reason = "Reason with @mentions #channels :emojis: and `code`"

        response_handler.create_embed = MockEmbedCreator()
        response_handler.send_embed = AsyncMock(return_value=MagicMock(spec=discord.Message))

        await response_handler.handle_case_response(
            ctx=mock_ctx,
            case_type=DBCaseType.WARN,
            case_number=1,
            reason=special_reason,
            user=mock_member,
            dm_sent=True,
        )

        create_call = response_handler.create_embed.call_history[0]
        fields = create_call['fields']

        # Reason field should contain the special characters
        reason_field = next(field for field in fields if field[0] == "Reason")
        assert reason_field[1] == f"-# > {special_reason}"

    @pytest.mark.unit
    async def test_case_response_handler_initialization(self) -> None:
        """Test CaseResponseHandler initialization."""
        handler = CaseResponseHandler()

        assert handler is not None
        assert hasattr(handler, 'handle_case_response')
        assert hasattr(handler, '_format_case_title')


class MockEmbedCreator:
    """Mock embed creator for testing."""

    def __init__(self):
        self.call_history = []

    def __call__(self, *args, **kwargs):
        """Make the mock callable like the real create_embed method."""
        return self.create_embed(**kwargs)

    def create_embed(self, **kwargs):
        """Mock create_embed method."""
        self.call_history.append(kwargs)

        # Create a mock embed with the requested properties
        mock_embed = MagicMock()
        mock_embed.title = kwargs.get('title', 'Mock Title')
        mock_embed.description = kwargs.get('description', '')
        mock_embed.color = kwargs.get('color', 0xFFFFFF)
        mock_embed.fields = []

        # Add fields if provided
        fields = kwargs.get('fields', [])
        for name, value, inline in fields:
            field_mock = MagicMock()
            field_mock.name = name
            field_mock.value = value
            field_mock.inline = inline
            mock_embed.fields.append(field_mock)

        return mock_embed
