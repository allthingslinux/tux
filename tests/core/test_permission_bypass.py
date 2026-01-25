"""Bot owner, sysadmin, and guild-owner permission bypass unit tests."""

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
    """Bot owner, sysadmin, and guild owner bypass behavior."""

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = REGULAR_USER_ID
        ctx.command = MagicMock()
        ctx.command.qualified_name = "test_command"
        return ctx

    @pytest.mark.asyncio
    async def test_bot_owner_bypasses_permission_check(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Bot owner can run protected commands without permission check."""
        # Arrange
        with patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID):
            mock_ctx.author.id = BOT_OWNER_ID

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act
            result = await test_command(mock_ctx)

            # Assert
            assert result == "success"

    @pytest.mark.asyncio
    async def test_sysadmin_bypasses_permission_check(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Sysadmin can run protected commands without permission check."""
        # Arrange
        with patch.object(
            CONFIG.USER_IDS,
            "SYSADMINS",
            [SYSADMIN_ID, SECOND_SYSADMIN_ID],
        ):
            mock_ctx.author.id = SYSADMIN_ID

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act
            result = await test_command(mock_ctx)

            # Assert
            assert result == "success"

    @pytest.mark.asyncio
    async def test_regular_user_raises_permission_denied_for_unconfigured_command(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Regular user (not owner/sysadmin) raises when command has no permission."""
        # Arrange
        mock_perm_system = AsyncMock()
        mock_perm_system.get_command_permission = AsyncMock(return_value=None)
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
            patch(
                "tux.core.decorators.get_permission_system",
                return_value=mock_perm_system,
                autospec=True,
            ),
        ):
            mock_ctx.author.id = REGULAR_USER_ID

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act & Assert
            with pytest.raises(TuxPermissionDeniedError):
                await test_command(mock_ctx)

    @pytest.mark.asyncio
    async def test_dm_context_bypasses_permission_check(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """DM context (no guild) bypasses permission check for any user."""
        # Arrange
        mock_ctx.guild = None
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
        ):
            mock_ctx.author.id = REGULAR_USER_ID

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act
            result = await test_command(mock_ctx)

            # Assert
            assert result == "success"

    @pytest.mark.asyncio
    async def test_guild_owner_bypasses_permission_check(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Guild owner can run protected commands without permission check."""
        # Arrange
        guild = cast(discord.Guild, mock_ctx.guild)
        guild.owner_id = GUILD_OWNER_ID
        mock_ctx.author.id = GUILD_OWNER_ID
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
        ):

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act
            result = await test_command(mock_ctx)

            # Assert
            assert result == "success"

    @pytest.mark.asyncio
    async def test_bot_owner_bypass_logs_debug_message(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Bot owner bypass emits a debug log containing bypass and user id."""
        # Arrange
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch(
                "tux.core.decorators.logger",
                autospec=True,
            ) as mock_logger,
        ):
            mock_ctx.author.id = BOT_OWNER_ID

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act
            await test_command(mock_ctx)

            # Assert
            mock_logger.debug.assert_called()
            call_args = mock_logger.debug.call_args[0][0]
            assert "bypassing permission check" in call_args
            assert str(BOT_OWNER_ID) in call_args

    @pytest.mark.asyncio
    async def test_guild_owner_bypass_logs_debug_message(
        self,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Guild owner bypass emits a debug log with guild owner and user id."""
        # Arrange
        guild = cast(discord.Guild, mock_ctx.guild)
        guild.owner_id = GUILD_OWNER_ID
        mock_ctx.author.id = GUILD_OWNER_ID
        with (
            patch.object(CONFIG.USER_IDS, "BOT_OWNER_ID", BOT_OWNER_ID),
            patch.object(CONFIG.USER_IDS, "SYSADMINS", [SYSADMIN_ID]),
            patch(
                "tux.core.decorators.logger",
                autospec=True,
            ) as mock_logger,
        ):

            @requires_command_permission()
            async def test_command(ctx: commands.Context[Tux]) -> str:
                return "success"

            # Act
            await test_command(mock_ctx)

            # Assert
            mock_logger.debug.assert_called()
            call_args = mock_logger.debug.call_args[0][0]
            assert "Guild owner" in call_args
            assert str(GUILD_OWNER_ID) in call_args
            assert "bypassing permission check" in call_args
