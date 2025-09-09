"""
🚀 ConditionChecker Unit Tests - Permission Decorator System

Tests for the ConditionChecker class that provides permission decorators
and advanced permission checking operations for moderation commands.

Test Coverage:
- Permission decorator creation and functionality
- Condition checking with permission system integration
- Advanced permission validation
- Decorator application to commands
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext import commands

from tux.services.moderation.condition_checker import ConditionChecker, require_moderator
from tux.core.types import Tux

# Mock the permission system at module level to avoid initialization issues
@pytest.fixture(autouse=True)
def mock_permission_system():
    """Mock the permission system globally for all tests."""
    with patch('tux.services.moderation.condition_checker.get_permission_system') as mock_get_perm:
        mock_perm_system = MagicMock()
        mock_perm_system.check_permission = AsyncMock()
        mock_perm_system.require_permission = AsyncMock()
        mock_get_perm.return_value = mock_perm_system
        yield mock_perm_system


class TestConditionChecker:
    """🛡️ Test ConditionChecker functionality."""

    @pytest.fixture
    def condition_checker(self) -> ConditionChecker:
        """Create a ConditionChecker instance for testing."""
        # The permission system is already mocked at module level
        return ConditionChecker()

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
    async def test_condition_checker_initialization(
        self,
        condition_checker: ConditionChecker,
    ) -> None:
        """Test ConditionChecker initialization and permission system integration."""
        assert condition_checker is not None
        assert hasattr(condition_checker, 'permission_system')
        assert condition_checker.permission_system is not None

    @pytest.mark.unit
    async def test_check_condition_success(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test successful condition checking."""
        # Mock permission system to return True
        condition_checker.permission_system.check_permission = AsyncMock(return_value=True)

        result = await condition_checker.check_condition(
            ctx=mock_ctx,
            target_user=mock_member,
            moderator=mock_ctx.author,
            action="ban",
        )

        assert result is True
        condition_checker.permission_system.check_permission.assert_called_once()

    @pytest.mark.unit
    async def test_check_condition_permission_denied(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test condition checking when permission is denied."""
        # Mock permission system to return False
        condition_checker.permission_system.check_permission = AsyncMock(return_value=False)

        result = await condition_checker.check_condition(
            ctx=mock_ctx,
            target_user=mock_member,
            moderator=mock_ctx.author,
            action="ban",
        )

        assert result is False

    @pytest.mark.unit
    async def test_check_condition_no_guild(
        self,
        condition_checker: ConditionChecker,
        mock_member: discord.Member,
    ) -> None:
        """Test condition checking when context has no guild."""
        # Create context without guild
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = None

        result = await condition_checker.check_condition(
            ctx=ctx,
            target_user=mock_member,
            moderator=MagicMock(),
            action="ban",
        )

        assert result is False
        # Permission system should not be called when no guild
        condition_checker.permission_system.check_permission.assert_not_called()

    @pytest.mark.unit
    async def test_check_condition_action_mapping(
        self,
        condition_checker: ConditionChecker,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test that different actions map to appropriate permission levels."""
        condition_checker.permission_system.check_permission = AsyncMock(return_value=True)

        # Test ban action (should map to MODERATOR level)
        await condition_checker.check_condition(
            ctx=mock_ctx,
            target_user=mock_member,
            moderator=mock_ctx.author,
            action="ban",
        )

        # Verify it was called with the correct permission level value
        from tux.core.permission_system import PermissionLevel
        call_args = condition_checker.permission_system.check_permission.call_args
        assert call_args[0][1] == PermissionLevel.MODERATOR.value

    @pytest.mark.unit
    async def test_permission_decorator_creation(self) -> None:
        """Test that permission decorators can be created."""
        # Test that we can import and create decorators
        from tux.services.moderation.condition_checker import (
            require_moderator,
            require_admin,
            require_junior_mod,
        )

        # These should be callable decorator functions
        assert callable(require_moderator)
        assert callable(require_admin)
        assert callable(require_junior_mod)

    @pytest.mark.unit
    async def test_decorator_application(
        self,
        mock_ctx: commands.Context[Tux],
        mock_member: discord.Member,
    ) -> None:
        """Test applying permission decorator to a command function."""
        # Create a mock command function
        async def mock_command(ctx: commands.Context[Tux], member: discord.Member) -> str:
            return f"Banned {member.name}"

        # Apply the decorator
        decorated_command = require_moderator()(mock_command)

        # Verify the decorated function is callable
        assert callable(decorated_command)

        # Mock the permission system to succeed
        with patch('tux.services.moderation.condition_checker.get_permission_system') as mock_get_perm:
            mock_perm_system = MagicMock()
            mock_perm_system.require_permission = AsyncMock(return_value=None)
            mock_get_perm.return_value = mock_perm_system

            # Call the decorated function
            result = await decorated_command(mock_ctx, mock_member)

            # Should return the original function's result
            assert result == f"Banned {mock_member.name}"
            from tux.core.permission_system import PermissionLevel
            mock_perm_system.require_permission.assert_called_once_with(mock_ctx, PermissionLevel.MODERATOR)
