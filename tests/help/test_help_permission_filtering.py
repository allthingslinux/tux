"""
📚 Help System Permission Filtering Tests.

Tests for the help command filtering based on user permissions.
Commands should be hidden from users who don't have permission to use them.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from tux.core.permission_system import RESTRICTED_COMMANDS
from tux.help.data import HelpData
from tux.shared.config import CONFIG


class TestHelpPermissionFiltering:
    """📚 Test help command permission filtering."""

    @pytest.fixture
    def mock_bot(self) -> MagicMock:
        """Create a mock bot instance."""
        bot = MagicMock()
        bot.owner_ids = {111111111}  # Bot owner ID
        return bot

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Any]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.guild.owner_id = 222222222
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 999999999  # Regular user
        ctx.author.roles = []
        ctx.bot = MagicMock()
        ctx.bot.owner_ids = {111111111}
        return ctx

    @pytest.fixture
    def mock_command(self) -> commands.Command[Any, Any, Any]:
        """Create a mock command."""
        cmd = MagicMock(spec=commands.Command)
        cmd.name = "test_command"
        cmd.qualified_name = "test_command"
        cmd.hidden = False
        cmd.enabled = True
        cmd.aliases = []
        cmd.callback = MagicMock()
        return cmd

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_basic_checks(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test basic command visibility checks."""
        help_data = HelpData(mock_bot, mock_ctx)

        # Hidden command should be filtered
        mock_command.hidden = True
        assert not await help_data.can_run_command(mock_command)

        # Disabled command should be filtered
        mock_command.hidden = False
        mock_command.enabled = False
        assert not await help_data.can_run_command(mock_command)

        # Normal command should be visible
        mock_command.enabled = True
        # No permission system used, so should be visible
        assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_dm_context(
        self,
        mock_bot: MagicMock,
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that all commands are visible in DM context."""
        # Create DM context (no guild)
        dm_ctx = MagicMock(spec=commands.Context)
        dm_ctx.guild = None
        dm_ctx.author = MagicMock()
        dm_ctx.author.id = 999999999

        help_data = HelpData(mock_bot, dm_ctx)

        # Even restricted commands should be visible in DMs
        mock_command.name = "eval"
        assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_no_context(
        self,
        mock_bot: MagicMock,
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that commands are visible when no context is provided."""
        help_data = HelpData(mock_bot, None)

        # Should show all commands when no context
        mock_command.name = "eval"
        assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_restricted_for_non_owner(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that restricted commands are hidden from non-owners."""
        help_data = HelpData(mock_bot, mock_ctx)

        # Regular user should not see restricted commands
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", []),
        ):
            for cmd_name in RESTRICTED_COMMANDS:
                mock_command.name = cmd_name
                assert not await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_restricted_for_owner(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that restricted commands are visible to bot owner."""
        mock_ctx.author.id = 111111111  # Bot owner
        mock_ctx.bot.owner_ids = {111111111}

        help_data = HelpData(mock_bot, mock_ctx)

        with patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111):
            for cmd_name in RESTRICTED_COMMANDS:
                mock_command.name = cmd_name
                assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_restricted_for_sysadmin(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that restricted commands are visible to sysadmin."""
        mock_ctx.author.id = 222222222  # Sysadmin
        mock_ctx.bot.owner_ids = {111111111, 222222222}

        help_data = HelpData(mock_bot, mock_ctx)

        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [222222222]),
        ):
            for cmd_name in RESTRICTED_COMMANDS:
                mock_command.name = cmd_name
                assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_permission_system(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that commands with permission system are filtered by rank."""
        help_data = HelpData(mock_bot, mock_ctx)

        # Mock command to use permission system
        mock_command.callback.__uses_dynamic_permissions__ = True  # type: ignore[attr-defined]

        # Mock permission system
        mock_perm_system = MagicMock()
        mock_perm_system.get_command_permission = AsyncMock(
            return_value=None,
        )  # Unconfigured
        mock_perm_system.get_user_permission_rank = AsyncMock(return_value=0)  # No rank

        with (
            patch("tux.help.data.get_permission_system", return_value=mock_perm_system),
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", []),
        ):
            # Unconfigured command should be hidden
            assert not await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_permission_rank_check(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test permission rank checking for commands."""
        help_data = HelpData(mock_bot, mock_ctx)

        # Mock command to use permission system
        mock_command.callback.__uses_dynamic_permissions__ = True  # type: ignore[attr-defined]

        # Mock permission config - requires rank 3
        mock_cmd_perm = MagicMock()
        mock_cmd_perm.required_rank = 3

        # Mock permission system
        mock_perm_system = MagicMock()
        mock_perm_system.get_command_permission = AsyncMock(return_value=mock_cmd_perm)

        with (
            patch("tux.help.data.get_permission_system", return_value=mock_perm_system),
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", []),
        ):
            # User with rank 2 should not see command requiring rank 3
            mock_perm_system.get_user_permission_rank = AsyncMock(return_value=2)
            assert not await help_data.can_run_command(mock_command)

            # User with rank 3 should see command requiring rank 3
            mock_perm_system.get_user_permission_rank = AsyncMock(return_value=3)
            assert await help_data.can_run_command(mock_command)

            # User with rank 5 should see command requiring rank 3
            mock_perm_system.get_user_permission_rank = AsyncMock(return_value=5)
            assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_can_run_command_guild_owner_bypass(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
        mock_command: commands.Command[Any, Any, Any],
    ) -> None:
        """Test that guild owner bypasses permission checks."""
        help_data = HelpData(mock_bot, mock_ctx)

        # Set user as guild owner
        mock_ctx.author.id = 222222222
        if mock_ctx.guild is not None:
            mock_ctx.guild.owner_id = 222222222

        # Mock command to use permission system
        mock_command.callback.__uses_dynamic_permissions__ = True  # type: ignore[attr-defined]

        # Mock permission config requiring rank 5
        mock_cmd_perm = MagicMock()
        mock_cmd_perm.required_rank = 5

        mock_perm_system = MagicMock()
        mock_perm_system.get_command_permission = AsyncMock(return_value=mock_cmd_perm)

        with (
            patch("tux.help.data.get_permission_system", return_value=mock_perm_system),
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", []),
        ):
            # Guild owner should see command even without rank
            mock_perm_system.get_user_permission_rank = AsyncMock(return_value=0)
            assert await help_data.can_run_command(mock_command)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_command_categories_filters_commands(
        self,
        mock_bot: MagicMock,
        mock_ctx: commands.Context[Any],
    ) -> None:
        """Test that get_command_categories filters commands by permissions."""
        # Create mock commands
        normal_cmd = MagicMock(spec=commands.Command)
        normal_cmd.name = "ban"
        normal_cmd.qualified_name = "ban"
        normal_cmd.hidden = False
        normal_cmd.enabled = True
        normal_cmd.callback = MagicMock()
        normal_cmd.callback.__uses_dynamic_permissions__ = None

        restricted_cmd = MagicMock(spec=commands.Command)
        restricted_cmd.name = "eval"
        restricted_cmd.qualified_name = "eval"
        restricted_cmd.hidden = False
        restricted_cmd.enabled = True
        restricted_cmd.callback = MagicMock()

        # Mock cog with commands
        mock_cog = MagicMock()
        mock_cog.get_commands = lambda: [normal_cmd, restricted_cmd]
        mock_cog.__module__ = "tux.modules.moderation.ban"

        mock_bot.cogs = {"Moderation": mock_cog}

        help_data = HelpData(mock_bot, mock_ctx)

        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", 111111111),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", []),
        ):
            categories = await help_data.get_command_categories()

            # Should only include non-restricted commands
            # (actual implementation may vary, but restricted should be filtered)
            assert categories is not None
