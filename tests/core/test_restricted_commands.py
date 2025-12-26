"""
🔒 Restricted Commands Unit Tests.

Tests for commands that are restricted from being assigned to permission ranks.
Restricted commands (eval, jsk, jishaku) are owner/sysadmin only and must not
be configurable via the permission system.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tux.core.permission_system import RESTRICTED_COMMANDS, PermissionSystem


class TestRestrictedCommands:
    """🔒 Test restricted commands functionality."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Create a mock bot instance."""
        return MagicMock()

    @pytest.fixture
    def mock_db_coordinator(self) -> MagicMock:
        """Create a mock database coordinator."""
        db_coordinator = MagicMock()
        db_coordinator.permission_ranks = MagicMock()
        db_coordinator.command_permissions = MagicMock()
        return db_coordinator

    @pytest.fixture
    def permission_system(
        self,
        mock_bot: MagicMock,
        mock_db_coordinator: MagicMock,
    ) -> PermissionSystem:
        """Create a PermissionSystem instance for testing."""
        return PermissionSystem(mock_bot, mock_db_coordinator)

    @pytest.mark.unit
    def test_restricted_commands_constant(self) -> None:
        """Test that RESTRICTED_COMMANDS contains expected commands."""
        assert "eval" in RESTRICTED_COMMANDS
        assert "e" in RESTRICTED_COMMANDS  # eval alias
        assert "jsk" in RESTRICTED_COMMANDS
        assert "jishaku" in RESTRICTED_COMMANDS

    @pytest.mark.unit
    def test_restricted_commands_is_frozen(self) -> None:
        """Test that RESTRICTED_COMMANDS is immutable."""
        # Should be a frozenset
        assert isinstance(RESTRICTED_COMMANDS, frozenset)
        # Attempting to add should raise AttributeError
        with pytest.raises(AttributeError):
            RESTRICTED_COMMANDS.add("test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_command_permission_blocks_restricted_commands(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test that setting permission for restricted commands raises ValueError."""
        guild_id = 123456789

        # Try to set permission for each restricted command
        for cmd_name in RESTRICTED_COMMANDS:
            with pytest.raises(ValueError, match="restricted"):
                await permission_system.set_command_permission(
                    guild_id=guild_id,
                    command_name=cmd_name,
                    required_rank=3,
                )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_command_permission_allows_normal_commands(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test that non-restricted commands can be assigned permissions."""
        guild_id = 123456789
        command_name = "ban"

        # Mock the database controller to return a permission
        mock_permission = MagicMock()
        mock_permission.guild_id = guild_id
        mock_permission.command_name = command_name
        mock_permission.required_rank = 3

        permission_system.db.command_permissions.set_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        # Should succeed for non-restricted command
        result = await permission_system.set_command_permission(
            guild_id=guild_id,
            command_name=command_name,
            required_rank=3,
        )

        assert result is not None
        assert result.command_name == command_name
        permission_system.db.command_permissions.set_command_permission.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_command_permission_case_insensitive(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test that restricted command checks are case-insensitive."""
        guild_id = 123456789

        # Try uppercase and mixed case
        test_cases = ["EVAL", "Eval", "JSK", "Jsk", "Jishaku", "JISHAKU"]

        for cmd_name in test_cases:
            with pytest.raises(ValueError, match="restricted"):
                await permission_system.set_command_permission(
                    guild_id=guild_id,
                    command_name=cmd_name,
                    required_rank=3,
                )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_from_config_skips_restricted_commands(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test that loading from config skips restricted commands."""
        guild_id = 123456789

        # Create a config with both normal and restricted commands
        config = {
            "command_permissions": [
                {"command": "ban", "rank": 3},
                {"command": "eval", "rank": 2},  # Restricted - should be skipped
                {"command": "kick", "rank": 2},
                {"command": "jsk", "rank": 5},  # Restricted - should be skipped
            ],
        }

        # Mock the database controller
        mock_permission = MagicMock()
        permission_system.db.command_permissions.set_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        # Mock logger to check for warning messages
        with patch("tux.core.permission_system.logger") as mock_logger:
            await permission_system.load_from_config(guild_id, config)

            # Should only call set_command_permission for non-restricted commands (ban, kick)
            assert (
                permission_system.db.command_permissions.set_command_permission.call_count
                == 2
            )

            # Should log warnings for restricted commands
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any("eval" in str(call).lower() for call in warning_calls)
            assert any("jsk" in str(call).lower() for call in warning_calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_from_config_processes_normal_commands(
        self,
        permission_system: PermissionSystem,
    ) -> None:
        """Test that loading from config processes normal commands correctly."""
        guild_id = 123456789

        config = {
            "command_permissions": [
                {"command": "ban", "rank": 3},
                {"command": "kick", "rank": 2},
            ],
        }

        mock_permission = MagicMock()
        permission_system.db.command_permissions.set_command_permission = AsyncMock(
            return_value=mock_permission,
        )

        await permission_system.load_from_config(guild_id, config)

        # Should process both commands
        assert (
            permission_system.db.command_permissions.set_command_permission.call_count
            == 2
        )

        # Verify correct calls
        calls = permission_system.db.command_permissions.set_command_permission.call_args_list
        command_names = [call[1]["command_name"] for call in calls]
        assert "ban" in command_names
        assert "kick" in command_names
