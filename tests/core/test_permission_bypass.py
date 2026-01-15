"""Unit tests for bot owner/sysadmin permission bypass."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.decorators import requires_command_permission
from tux.shared.config import CONFIG
from tux.shared.exceptions import TuxPermissionDeniedError

pytestmark = pytest.mark.unit

BOT_OWNER_ID = 111111111
SYSADMIN_ID = 222222222
SECOND_SYSADMIN_ID = 333333333
REGULAR_USER_ID = 999999999
GUILD_OWNER_ID = 444444444


class TestPermissionBypass:
    """Test bot owner and sysadmin permission bypass functionality."""

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock()
        ctx.guild.id = 123456789
        ctx.author = MagicMock()
        ctx.author.id = REGULAR_USER_ID  # Regular user
        ctx.command = MagicMock()
        ctx.command.qualified_name = "test_command"
        return ctx

    @pytest.mark.asyncio
    async def test_bot_owner_bypasses_permission(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that bot owner bypasses permission checks."""
        # Set up bot owner ID
        with patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID):
            mock_ctx.author.id = BOT_OWNER_ID  # User is bot owner

            # Create a simple command with permission requirement
            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Execute command - should bypass permission check entirely
            result = await test_command(mock_ctx)

            assert result == "success"

    @pytest.mark.asyncio
    async def test_sysadmin_bypasses_permission(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that sysadmin bypasses permission checks."""
        # Set up sysadmin list
        with patch.object(
            CONFIG.USER_IDS,
            "SYSADMINS",
            [SYSADMIN_ID, SECOND_SYSADMIN_ID],
        ):
            mock_ctx.author.id = SYSADMIN_ID  # User is sysadmin

            # Create a simple command with permission requirement
            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Execute command - should bypass permission check entirely
            result = await test_command(mock_ctx)

            assert result == "success"

    @pytest.mark.asyncio
    async def test_regular_user_checked_for_permission(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that regular users are subject to permission checks."""
        # Ensure user is neither bot owner nor sysadmin
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
        ):
            mock_ctx.author.id = REGULAR_USER_ID  # Regular user

            # Create a command with permission requirement
            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Mock the permission system to return None (unconfigured command)
            with patch("tux.core.decorators.get_permission_system") as mock_get_perm:
                mock_perm_system = AsyncMock()
                mock_perm_system.get_command_permission = AsyncMock(return_value=None)
                mock_get_perm.return_value = mock_perm_system

                # Should raise permission denied for unconfigured command
                with pytest.raises(TuxPermissionDeniedError):
                    await test_command(mock_ctx)

    @pytest.mark.asyncio
    async def test_dm_bypass_still_works(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that DMs still bypass permission checks (no guild)."""
        mock_ctx.guild = None  # DM context

        # User is regular user (not owner/sysadmin)
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
        ):
            mock_ctx.author.id = REGULAR_USER_ID

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # DMs should bypass without checking permissions
            result = await test_command(mock_ctx)
            assert result == "success"

    @pytest.mark.asyncio
    async def test_guild_owner_bypasses_permission(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that guild owner bypasses permission checks."""
        # Set up guild owner
        guild = cast(discord.Guild, mock_ctx.guild)
        guild.owner_id = GUILD_OWNER_ID
        mock_ctx.author.id = GUILD_OWNER_ID  # User is guild owner

        # Ensure user is not bot owner or sysadmin
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
        ):

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Execute command - should bypass permission check entirely
            result = await test_command(mock_ctx)

            assert result == "success"

    @pytest.mark.asyncio
    async def test_bypass_logs_debug_message(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that owner/sysadmin bypass logs a debug message."""
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch("tux.core.decorators.logger") as mock_logger,
        ):
            mock_ctx.author.id = BOT_OWNER_ID  # Bot owner

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            await test_command(mock_ctx)

            # Verify debug log was called
            mock_logger.debug.assert_called()
            call_args = mock_logger.debug.call_args[0][0]
            assert "bypassing permission check" in call_args
        assert str(BOT_OWNER_ID) in call_args

    @pytest.mark.asyncio
    async def test_guild_owner_bypass_logs_debug_message(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that guild owner bypass logs a debug message."""
        guild = cast(discord.Guild, mock_ctx.guild)
        guild.owner_id = GUILD_OWNER_ID
        mock_ctx.author.id = GUILD_OWNER_ID  # User is guild owner

        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
            patch("tux.core.decorators.logger") as mock_logger,
        ):

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            await test_command(mock_ctx)

            # Verify debug log was called
            mock_logger.debug.assert_called()
            call_args = mock_logger.debug.call_args[0][0]
            assert "Guild owner" in call_args
            assert str(GUILD_OWNER_ID) in call_args
            assert "bypassing permission check" in call_args
