"""
🚀 DMHandler Unit Tests - Direct Message Operations

Tests for the DMHandler mixin that manages direct message operations
for moderation actions.

Test Coverage:
- DM sending functionality
- Error handling for DM failures
- Silent mode behavior
- DM result processing
- User communication patterns
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands

from tux.services.moderation.dm_handler import DMHandler
from tux.core.types import Tux


class TestDMHandler:
    """💬 Test DMHandler functionality."""

    @pytest.fixture
    def dm_handler(self) -> DMHandler:
        """Create a DMHandler instance for testing."""
        return DMHandler()

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.name = "Test Guild"
        ctx.guild.__str__ = MagicMock(return_value="Test Guild")  # For string representation
        ctx.bot = MagicMock(spec=Tux)
        return ctx

    @pytest.fixture
    def mock_member(self) -> discord.Member:
        """Create a mock Discord member."""
        member = MagicMock(spec=discord.Member)
        member.id = 123456789
        member.name = "TestUser"
        member.send = AsyncMock()
        return member

    @pytest.fixture
    def mock_user(self) -> discord.User:
        """Create a mock Discord user."""
        user = MagicMock(spec=discord.User)
        user.id = 987654321
        user.name = "TestUser"
        user.send = AsyncMock()
        return user

    @pytest.mark.unit
    async def test_send_dm_successful(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test successful DM sending."""
        mock_member.send.return_value = None  # Successful send

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="Test reason",
            action="banned",
        )

        assert result is True
        mock_member.send.assert_called_once_with(
            "You have been banned from Test Guild for the following reason:\n> Test reason",
        )

    @pytest.mark.unit
    async def test_send_dm_silent_mode(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending in silent mode."""
        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=True,
            user=mock_member,
            reason="Test reason",
            action="banned",
        )

        assert result is False
        mock_member.send.assert_not_called()

    @pytest.mark.unit
    async def test_send_dm_forbidden_error(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending when user has DMs disabled."""
        mock_member.send.side_effect = discord.Forbidden(MagicMock(), "Cannot send messages to this user")

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="Test reason",
            action="banned",
        )

        assert result is False
        mock_member.send.assert_called_once()

    @pytest.mark.unit
    async def test_send_dm_http_exception(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending with HTTP exception."""
        mock_member.send.side_effect = discord.HTTPException(MagicMock(), "Network error")

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="Test reason",
            action="banned",
        )

        assert result is False
        mock_member.send.assert_called_once()

    @pytest.mark.unit
    async def test_send_dm_user_object(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_user: discord.User,
    ) -> None:
        """Test DM sending to User object (not Member)."""
        mock_user.send.return_value = None

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_user,
            reason="Test reason",
            action="banned",
        )

        assert result is True
        mock_user.send.assert_called_once_with(
            "You have been banned from Test Guild for the following reason:\n> Test reason",
        )

    @pytest.mark.unit
    async def test_send_dm_custom_action(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending with custom action message."""
        mock_member.send.return_value = None

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="Custom reason",
            action="temporarily muted",
        )

        assert result is True
        mock_member.send.assert_called_once_with(
            "You have been temporarily muted from Test Guild for the following reason:\n> Custom reason",
        )

    @pytest.mark.unit
    async def test_send_dm_special_characters_in_reason(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending with special characters in reason."""
        mock_member.send.return_value = None

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="Reason with @mentions #channels and :emojis:",
            action="warned",
        )

        assert result is True
        expected_message = (
            "You have been warned from Test Guild for the following reason:\n"
            "> Reason with @mentions #channels and :emojis:"
        )
        mock_member.send.assert_called_once_with(expected_message)

    @pytest.mark.unit
    async def test_handle_dm_result_success(self, dm_handler: DMHandler, mock_member: discord.Member) -> None:
        """Test _handle_dm_result with successful DM."""
        result = dm_handler._handle_dm_result(mock_member, True)
        assert result is True

    @pytest.mark.unit
    async def test_handle_dm_result_failure(self, dm_handler: DMHandler, mock_member: discord.Member) -> None:
        """Test _handle_dm_result with failed DM."""
        result = dm_handler._handle_dm_result(mock_member, False)
        assert result is False

    @pytest.mark.unit
    async def test_handle_dm_result_exception(self, dm_handler: DMHandler, mock_member: discord.Member) -> None:
        """Test _handle_dm_result with exception result."""
        exception = discord.Forbidden(MagicMock(), "DM blocked")
        result = dm_handler._handle_dm_result(mock_member, exception)
        assert result is False

    @pytest.mark.unit
    async def test_handle_dm_result_none(self, dm_handler: DMHandler, mock_member: discord.Member) -> None:
        """Test _handle_dm_result with None result."""
        result = dm_handler._handle_dm_result(mock_member, None)
        assert result is False

    @pytest.mark.unit
    async def test_send_dm_empty_reason(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending with empty reason."""
        mock_member.send.return_value = None

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="",
            action="kicked",
        )

        assert result is True
        mock_member.send.assert_called_once_with(
            "You have been kicked from Test Guild for the following reason:\n> ",
        )

    @pytest.mark.unit
    async def test_send_dm_long_reason(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending with very long reason."""
        long_reason = "A" * 1000  # Very long reason
        mock_member.send.return_value = None

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason=long_reason,
            action="banned",
        )

        assert result is True
        expected_message = f"You have been banned from Test Guild for the following reason:\n> {long_reason}"
        mock_member.send.assert_called_once_with(expected_message)

    @pytest.mark.unit
    async def test_send_dm_guild_without_name(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test DM sending when guild has no name."""
        mock_ctx.guild.name = None
        # Update __str__ to reflect None name (mock behavior)
        mock_ctx.guild.__str__ = MagicMock(return_value="<MagicMock spec='Guild' id='123456789'>")
        mock_member.send.return_value = None

        result = await dm_handler.send_dm(
            ctx=mock_ctx,
            silent=False,
            user=mock_member,
            reason="Test reason",
            action="banned",
        )

        assert result is True
        mock_member.send.assert_called_once_with(
            "You have been banned from <MagicMock spec='Guild' id='123456789'> for the following reason:\n> Test reason",
        )

    @pytest.mark.unit
    async def test_send_dm_multiple_calls(
        self,
        dm_handler: DMHandler,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test multiple DM sends to same user."""
        mock_member.send.return_value = None

        # Send multiple DMs
        result1 = await dm_handler.send_dm(mock_ctx, False, mock_member, "Reason 1", "warned")
        result2 = await dm_handler.send_dm(mock_ctx, False, mock_member, "Reason 2", "banned")

        assert result1 is True
        assert result2 is True
        assert mock_member.send.call_count == 2
