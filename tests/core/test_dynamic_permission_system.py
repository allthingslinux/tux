"""
🚀 Dynamic Permission System Unit Tests.

Tests for the new fully dynamic, database-driven permission system.

Test Coverage:
- Permission rank retrieval based on roles
- Dynamic decorator functionality (@requires_command_permission)
- Permission caching behavior
- Error handling (TuxPermissionDeniedError)
- Support for prefix, app, and hybrid commands
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.permission_system import PermissionSystem
from tux.database.controllers import DatabaseCoordinator
from tux.shared.exceptions import TuxPermissionDeniedError


class TestPermissionSystem:
    """🛡️ Test PermissionSystem core functionality."""

    @pytest.fixture
    def mock_bot(self) -> Tux:
        """Create a mock bot instance."""
        return MagicMock(spec=Tux)

    @pytest.fixture
    def mock_db_coordinator(self) -> MagicMock:
        """Create a mock database coordinator."""
        db_coordinator = MagicMock(spec=DatabaseCoordinator)
        db_coordinator.permission_ranks = MagicMock()
        return db_coordinator

    @pytest.fixture
    def permission_system(
        self,
        mock_bot: Tux,
        mock_db_coordinator: MagicMock,
    ) -> PermissionSystem:
        """Create a PermissionSystem instance for testing."""
        return PermissionSystem(mock_bot, mock_db_coordinator)

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 987654321
        ctx.author.roles = []
        ctx.bot = MagicMock(spec=Tux)
        return ctx

    @pytest.mark.unit
    async def test_permission_system_initialization(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test PermissionSystem initialization."""
        assert permission_system is not None
        assert hasattr(permission_system, "db")
        assert hasattr(permission_system, "bot")
        assert hasattr(permission_system, "_default_ranks")

    @pytest.mark.unit
    async def test_get_user_permission_rank_no_roles(
        self,
        permission_system: PermissionSystem,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test permission rank for user with no roles."""
        # Mock database to return 0 for no roles
        permission_system.db.permission_assignments.get_user_permission_rank = (
            AsyncMock(
                return_value=0,
            )
        )

        rank = await permission_system.get_user_permission_rank(mock_ctx)

        assert rank == 0
        permission_system.db.permission_assignments.get_user_permission_rank.assert_called_once()

    @pytest.mark.unit
    async def test_get_user_permission_rank_with_roles(
        self,
        permission_system: PermissionSystem,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test permission rank for user with assigned roles."""
        # Give user some roles
        mock_role_1 = MagicMock()
        mock_role_1.id = 111111
        mock_role_2 = MagicMock()
        mock_role_2.id = 222222
        mock_ctx.author.roles = [mock_role_1, mock_role_2]

        # Mock database to return rank 3 (highest from their roles)
        permission_system.db.permission_assignments.get_user_permission_rank = (
            AsyncMock(
                return_value=3,
            )
        )

        rank = await permission_system.get_user_permission_rank(mock_ctx)

        assert rank == 3
        # Verify it was called with correct role IDs
        call_args = permission_system.db.permission_assignments.get_user_permission_rank.call_args
        assert mock_ctx.guild is not None  # Ensure guild exists
        assert call_args[0][0] == mock_ctx.guild.id
        assert call_args[0][1] == mock_ctx.author.id
        assert 111111 in call_args[0][2]
        assert 222222 in call_args[0][2]

    @pytest.mark.unit
    async def test_get_user_permission_rank_no_guild(
        self,
        permission_system: PermissionSystem,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test permission rank when context has no guild (DMs)."""
        mock_ctx.guild = None

        rank = await permission_system.get_user_permission_rank(mock_ctx)

        # Should return 0 for DMs/non-guild contexts
        assert rank == 0

    @pytest.mark.unit
    async def test_get_command_permission(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test getting command permission configuration."""
        guild_id = 123456789
        command_name = "ban"

        # Mock database to return command permission
        mock_permission = MagicMock()
        mock_permission.permission_rank = 2
        permission_system.db.command_permissions.get_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        result = await permission_system.get_command_permission(guild_id, command_name)

        assert result is not None
        assert result.permission_rank == 2
        permission_system.db.command_permissions.get_command_permission.assert_called_once_with(
            guild_id,
            command_name,
        )

    @pytest.mark.unit
    async def test_get_command_permission_not_configured(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test getting command permission when not configured."""
        guild_id = 123456789
        command_name = "unknown_command"

        # Mock database to return None (not configured)
        permission_system.db.command_permissions.get_command_permission = AsyncMock(
            return_value=None,
        )

        result = await permission_system.get_command_permission(guild_id, command_name)

        # Should return None for unconfigured commands
        assert result is None


class TestPermissionDecorator:
    """🎯 Test @requires_command_permission decorator metadata."""

    @pytest.mark.unit
    def test_decorator_preserves_function_metadata(
        self,
    ) -> None:
        """Test that decorator preserves function name and docstring."""

        @requires_command_permission()
        async def my_special_command(ctx: commands.Context[Tux]) -> None:
            """This is my special command."""  # noqa: D401, D404

        # Should preserve function metadata
        assert my_special_command.__name__ == "my_special_command"
        assert my_special_command.__doc__ == "This is my special command."

    @pytest.mark.unit
    def test_decorator_is_callable(
        self,
    ) -> None:
        """Test that the decorator can be applied to functions."""

        @requires_command_permission()
        async def test_command(ctx: commands.Context[Tux]) -> str:
            return "test"

        # Should be callable
        assert callable(test_command)
        # Should be a coroutine function
        assert asyncio.iscoroutinefunction(test_command)


class TestPermissionError:
    """❌ Test TuxPermissionDeniedError exception."""

    @pytest.mark.unit
    def test_permission_error_with_command_name(self) -> None:
        """Test error message includes command name."""
        error = TuxPermissionDeniedError(
            required_rank=5,
            user_rank=2,
            command_name="ban",
        )

        error_msg = str(error)
        assert "5" in error_msg
        assert "2" in error_msg
        assert "ban" in error_msg

    @pytest.mark.unit
    def test_permission_error_without_command_name(self) -> None:
        """Test error message without command name."""
        error = TuxPermissionDeniedError(
            required_rank=3,
            user_rank=1,
            command_name=None,
        )

        error_msg = str(error)
        assert "3" in error_msg
        assert "1" in error_msg

    @pytest.mark.unit
    def test_permission_error_attributes(self) -> None:
        """Test error has correct attributes."""
        error = TuxPermissionDeniedError(
            required_rank=4,
            user_rank=2,
            command_name="kick",
        )

        assert error.required_rank == 4
        assert error.user_rank == 2
        assert error.command_name == "kick"
