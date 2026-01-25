"""Restricted commands unit tests.

Commands in RESTRICTED_COMMANDS (eval, e, jsk, jishaku) cannot be assigned to
permission ranks; they remain owner/sysadmin only.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tux.core.bot import Tux
from tux.core.permission_system import RESTRICTED_COMMANDS, PermissionSystem
from tux.database.controllers import DatabaseCoordinator
from tux.database.models import PermissionCommand


class TestRestrictedCommands:
    """Restricted commands constant and permission-system behavior."""

    @pytest.fixture
    def mock_bot(self) -> Tux:
        """Create a mock bot instance."""
        return MagicMock(spec=Tux)

    @pytest.fixture
    def mock_db_coordinator(self) -> MagicMock:
        """Create a mock database coordinator."""
        db_coordinator = MagicMock(spec=DatabaseCoordinator)
        db_coordinator.permission_ranks = MagicMock()
        db_coordinator.command_permissions = MagicMock()
        return db_coordinator

    @pytest.fixture
    def permission_system(
        self,
        mock_bot: Tux,
        mock_db_coordinator: MagicMock,
    ) -> PermissionSystem:
        """Create a PermissionSystem instance for testing."""
        PermissionSystem._command_permission_cache.clear()
        return PermissionSystem(mock_bot, mock_db_coordinator)

    @pytest.mark.unit
    def test_restricted_commands_contains_eval_e_jsk_jishaku(self) -> None:
        """RESTRICTED_COMMANDS includes eval, e, jsk, and jishaku."""
        # Act & Assert
        assert "eval" in RESTRICTED_COMMANDS
        assert "e" in RESTRICTED_COMMANDS
        assert "jsk" in RESTRICTED_COMMANDS
        assert "jishaku" in RESTRICTED_COMMANDS

    @pytest.mark.unit
    def test_restricted_commands_is_immutable_frozenset(self) -> None:
        """RESTRICTED_COMMANDS is a frozenset; add raises AttributeError."""
        # Act & Assert
        assert isinstance(RESTRICTED_COMMANDS, frozenset)
        with pytest.raises(AttributeError):
            RESTRICTED_COMMANDS.add("test")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("command_name", list(RESTRICTED_COMMANDS))
    @pytest.mark.unit
    async def test_set_command_permission_raises_for_restricted_command(
        self,
        permission_system: PermissionSystem,
        command_name: str,
    ) -> None:
        """Setting permission for a restricted command raises ValueError."""
        # Arrange
        guild_id = 123456789

        # Act & Assert
        with pytest.raises(ValueError, match="restricted"):
            await permission_system.set_command_permission(
                guild_id=guild_id,
                command_name=command_name,
                required_rank=3,
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_set_command_permission_returns_permission_for_normal_command(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Non-restricted commands can be assigned permissions; returns permission."""
        # Arrange
        guild_id = 123456789
        command_name = "ban"
        mock_permission = MagicMock(spec=PermissionCommand)
        mock_permission.guild_id = guild_id
        mock_permission.command_name = command_name
        mock_permission.required_rank = 3
        permission_system.db.command_permissions.set_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        # Act
        result = await permission_system.set_command_permission(
            guild_id=guild_id,
            command_name=command_name,
            required_rank=3,
        )

        # Assert
        assert result is not None
        assert result.command_name == command_name
        assert result.required_rank == 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command_name",
        ["EVAL", "Eval", "JSK", "Jsk", "Jishaku", "JISHAKU"],
    )
    @pytest.mark.unit
    async def test_set_command_permission_restricted_check_case_insensitive(
        self,
        permission_system: PermissionSystem,
        command_name: str,
    ) -> None:
        """Restricted command check is case-insensitive."""
        # Arrange
        guild_id = 123456789

        # Act & Assert
        with pytest.raises(ValueError, match="restricted"):
            await permission_system.set_command_permission(
                guild_id=guild_id,
                command_name=command_name,
                required_rank=3,
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_load_from_config_skips_restricted_and_processes_others(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """load_from_config processes only non-restricted commands and logs skip warnings."""
        # Arrange
        guild_id = 123456789
        config = {
            "command_permissions": [
                {"command": "ban", "rank": 3},
                {"command": "eval", "rank": 2},
                {"command": "kick", "rank": 2},
                {"command": "jsk", "rank": 5},
            ],
        }
        mock_permission = MagicMock(spec=PermissionCommand)
        permission_system.db.command_permissions.set_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        # Act
        with patch(
            "tux.core.permission_system.logger",
            autospec=True,
        ) as mock_logger:
            await permission_system.load_from_config(guild_id, config)

            # Assert - only ban and kick processed
            calls = permission_system.db.command_permissions.set_command_permission.call_args_list
            command_names = [c[1]["command_name"] for c in calls]
            assert set(command_names) == {"ban", "kick"}

            # Assert - warnings logged for restricted commands
            warning_calls = [c[0][0] for c in mock_logger.warning.call_args_list]
            assert any("eval" in str(m).lower() for m in warning_calls)
            assert any("jsk" in str(m).lower() for m in warning_calls)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_load_from_config_processes_all_normal_commands(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """load_from_config processes all commands when none are restricted."""
        # Arrange
        guild_id = 123456789
        config = {
            "command_permissions": [
                {"command": "ban", "rank": 3},
                {"command": "kick", "rank": 2},
            ],
        }
        mock_permission = MagicMock(spec=PermissionCommand)
        permission_system.db.command_permissions.set_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        # Act
        await permission_system.load_from_config(guild_id, config)

        # Assert
        calls = permission_system.db.command_permissions.set_command_permission.call_args_list
        command_names = [c[1]["command_name"] for c in calls]
        assert set(command_names) == {"ban", "kick"}
