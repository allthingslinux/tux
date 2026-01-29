"""Dynamic Permission System unit tests.

Tests for the database-driven permission system: rank retrieval, decorator
metadata, and TuxPermissionDeniedError behavior.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.permission_system import PermissionSystem
from tux.database.controllers import DatabaseCoordinator
from tux.database.models import PermissionCommand
from tux.shared.exceptions import TuxPermissionDeniedError

TEST_GUILD_ID = 123456789
TEST_USER_ID = 987654321


class TestPermissionSystem:
    """Test PermissionSystem core behavior."""

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
        ctx.guild.id = TEST_GUILD_ID
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = TEST_USER_ID
        ctx.author.roles = []
        ctx.bot = MagicMock(spec=Tux)
        return ctx

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permission_rank_returns_zero_when_user_has_no_roles(
        self,
        permission_system: PermissionSystem,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """User with no assigned roles receives permission rank 0."""
        # Arrange
        permission_system.db.permission_assignments.get_user_permission_rank = (
            AsyncMock(return_value=0)
        )

        # Act
        rank = await permission_system.get_user_permission_rank(mock_ctx)

        # Assert
        assert rank == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permission_rank_returns_highest_rank_from_user_roles(
        self,
        permission_system: PermissionSystem,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """User with assigned roles receives highest rank among those roles."""
        # Arrange
        mock_role_1 = MagicMock(spec=discord.Role)
        mock_role_1.id = 111111
        mock_role_2 = MagicMock(spec=discord.Role)
        mock_role_2.id = 222222
        mock_ctx.author.roles = [mock_role_1, mock_role_2]
        permission_system.db.permission_assignments.get_user_permission_rank = (
            AsyncMock(return_value=3)
        )

        # Act
        rank = await permission_system.get_user_permission_rank(mock_ctx)

        # Assert
        assert rank == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permission_rank_returns_zero_when_no_guild(
        self,
        permission_system: PermissionSystem,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """DM or non-guild context yields permission rank 0."""
        # Arrange
        mock_ctx.guild = None

        # Act
        rank = await permission_system.get_user_permission_rank(mock_ctx)

        # Assert
        assert rank == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_command_permission_returns_configured_required_rank(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Configured command returns its required rank and name."""
        # Arrange
        guild_id = 123456789
        command_name = "ban"
        mock_permission = MagicMock(spec=PermissionCommand)
        mock_permission.required_rank = 2
        mock_permission.command_name = command_name
        permission_system.db.command_permissions.get_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        # Act
        result = await permission_system.get_command_permission(guild_id, command_name)

        # Assert
        assert result is not None
        assert result.required_rank == 2
        assert result.command_name == command_name

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_command_permission_returns_none_when_not_configured(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Unconfigured command returns None."""
        # Arrange
        guild_id = 123456789
        command_name = "unknown_command"
        permission_system.db.command_permissions.get_command_permission = AsyncMock(
            return_value=None,
        )

        # Act
        result = await permission_system.get_command_permission(guild_id, command_name)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_command_permission_falls_back_to_parent_for_subcommand(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Subcommand without config uses parent command permission."""
        # Arrange
        guild_id = 123456789
        subcommand_name = "config ranks init"
        mock_parent = MagicMock(spec=PermissionCommand)
        mock_parent.command_name = "config"
        mock_parent.required_rank = 5
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_parent]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        permission_system.db.command_permissions.db.session = MagicMock(
            return_value=mock_session,
        )

        # Act
        result = await permission_system.get_command_permission(
            guild_id,
            subcommand_name,
        )

        # Assert
        assert result is not None
        assert result.required_rank == 5
        assert result.command_name == "config"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_command_permission_prefers_subcommand_over_parent(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Configured subcommand overrides parent command permission."""
        # Arrange
        guild_id = 123456789
        subcommand_name = "config ranks init"
        mock_sub = MagicMock(spec=PermissionCommand)
        mock_sub.command_name = subcommand_name
        mock_sub.required_rank = 7
        mock_parent = MagicMock(spec=PermissionCommand)
        mock_parent.command_name = "config"
        mock_parent.required_rank = 5
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_sub,
            mock_parent,
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        permission_system.db.command_permissions.db.session = MagicMock(
            return_value=mock_session,
        )

        # Act
        result = await permission_system.get_command_permission(
            guild_id,
            subcommand_name,
        )

        # Assert
        assert result is not None
        assert result.required_rank == 7
        assert result.command_name == subcommand_name


class TestPermissionDecorator:
    """Test @requires_command_permission decorator metadata."""

    @pytest.mark.unit
    def test_decorator_preserves_function_name_and_docstring(self) -> None:
        """Decorator preserves wrapped function name and docstring."""

        # Arrange & Act
        @requires_command_permission()
        async def my_special_command(ctx: commands.Context[Tux]) -> None:
            """This is my special command."""  # noqa: D401, D404

        # Assert
        assert my_special_command.__name__ == "my_special_command"
        assert my_special_command.__doc__ == "This is my special command."

    @pytest.mark.unit
    def test_decorator_produces_callable_coroutine_function(self) -> None:
        """Decorator yields a callable that is a coroutine function."""

        # Arrange & Act
        @requires_command_permission()
        async def test_command(ctx: commands.Context[Tux]) -> str:
            return "test"

        # Assert
        assert callable(test_command)
        assert inspect.iscoroutinefunction(test_command)


class TestPermissionError:
    """Test TuxPermissionDeniedError behavior."""

    @pytest.mark.parametrize(
        ("required_rank", "user_rank", "command_name", "expected_substrings"),
        [
            (5, 2, "ban", ["5", "2", "ban"]),
            (3, 1, None, ["3", "1"]),
        ],
    )
    @pytest.mark.unit
    def test_permission_error_message_includes_rank_and_command_when_provided(
        self,
        required_rank: int,
        user_rank: int,
        command_name: str | None,
        expected_substrings: list[str],
    ) -> None:
        """Error message includes required rank, user rank, and command name when set."""
        # Arrange
        error = TuxPermissionDeniedError(
            required_rank=required_rank,
            user_rank=user_rank,
            command_name=command_name,
        )

        # Act
        error_msg = str(error)

        # Assert
        for substring in expected_substrings:
            assert str(substring) in error_msg

    @pytest.mark.unit
    def test_permission_error_exposes_required_rank_user_rank_and_command_name(
        self,
    ) -> None:
        """Error exposes required_rank, user_rank, and command_name attributes."""
        # Arrange & Act
        error = TuxPermissionDeniedError(
            required_rank=4,
            user_rank=2,
            command_name="kick",
        )

        # Assert
        assert error.required_rank == 4
        assert error.user_rank == 2
        assert error.command_name == "kick"
