"""Purge command tests.

Tests real-world purge scenarios: limit validation, channel handling,
permission errors, and Discord API failure modes.
"""

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.modules.moderation.purge import Purge

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_bot() -> Tux:
    """Return a mock Tux bot with emoji_manager stubbed."""
    bot = MagicMock(spec=Tux)
    bot.emoji_manager = MagicMock()
    return bot


@pytest.fixture
def purge_cog(mock_bot: Tux) -> Purge:
    """Return a Purge cog with a mocked database coordinator."""
    cog = Purge(mock_bot)
    cog._db_coordinator = MagicMock()
    # discord.ext.commands.Command.__call__ only prepends self.cog when set.
    cog.prefix_purge.cog = cog
    return cog


@pytest.fixture
def mock_ctx(mock_bot: Tux) -> commands.Context[Tux]:
    """Return a mock command context in a text channel."""
    ctx = MagicMock(spec=commands.Context)
    ctx.bot = mock_bot
    ctx.guild = MagicMock(spec=discord.Guild)
    ctx.guild.id = 123456
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = 789012
    ctx.channel = MagicMock(spec=discord.TextChannel)
    ctx.message = MagicMock()
    ctx.message.delete = AsyncMock()
    ctx.send = AsyncMock()
    return ctx


class TestPurgeLimitValidation:
    """Purge should reject invalid message counts before touching Discord API."""

    async def test_zero_messages_rejected(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Purging 0 messages should be rejected."""
        await purge_cog.prefix_purge(mock_ctx, 0)

        mock_ctx.send.assert_called_once()
        assert "invalid" in mock_ctx.send.call_args[0][0].lower()

    async def test_negative_limit_rejected(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Purging negative messages should be rejected."""
        await purge_cog.prefix_purge(mock_ctx, -5)

        mock_ctx.send.assert_called_once()
        assert "invalid" in mock_ctx.send.call_args[0][0].lower()

    async def test_over_500_rejected(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Purging more than 500 messages should be rejected."""
        await purge_cog.prefix_purge(mock_ctx, 501)

        mock_ctx.send.assert_called_once()
        assert "500" in mock_ctx.send.call_args[0][0]

    async def test_valid_limit_proceeds(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """A valid limit (1-500) should attempt the purge."""
        mock_ctx.channel.purge = AsyncMock(return_value=[MagicMock()] * 10)

        await purge_cog.prefix_purge(mock_ctx, 10)

        mock_ctx.message.delete.assert_called_once()
        mock_ctx.channel.purge.assert_called_once()


class TestPurgeChannelHandling:
    """Purge should handle channel targeting correctly."""

    async def test_defaults_to_current_channel(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """When no channel specified, purge should use the current channel."""
        mock_ctx.channel.purge = AsyncMock(return_value=[MagicMock()] * 5)

        await purge_cog.prefix_purge(mock_ctx, 5, None)

        mock_ctx.channel.purge.assert_called_once()

    async def test_explicit_channel_used(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """When a channel is specified, purge should target that channel."""
        target_channel = MagicMock(spec=discord.TextChannel)
        target_channel.purge = AsyncMock(return_value=[MagicMock()] * 5)
        target_channel.mention = "#other-channel"

        await purge_cog.prefix_purge(mock_ctx, 5, target_channel)

        target_channel.purge.assert_called_once()
        mock_ctx.channel.purge.assert_not_called()

    async def test_invalid_channel_type_rejected(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Purge in a DM or non-text channel should be rejected."""
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)

        await purge_cog.prefix_purge(mock_ctx, 5, None)

        mock_ctx.send.assert_called_once()
        assert "invalid channel" in mock_ctx.send.call_args[0][0].lower()


class TestPurgeErrorHandling:
    """Purge should handle Discord API failures gracefully."""

    async def test_forbidden_shows_permission_error(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """When bot lacks permissions, user should get a clear error."""
        mock_ctx.channel.purge = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "Missing Permissions"),
        )

        await purge_cog.prefix_purge(mock_ctx, 5)

        mock_ctx.send.assert_called()
        assert "permission" in mock_ctx.send.call_args[0][0].lower()

    async def test_http_error_shows_error_message(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """HTTP errors from Discord should be reported to the user."""
        mock_ctx.channel.purge = AsyncMock(
            side_effect=discord.HTTPException(MagicMock(), "Rate limited"),
        )

        await purge_cog.prefix_purge(mock_ctx, 5)

        mock_ctx.send.assert_called()
        assert "error" in mock_ctx.send.call_args[0][0].lower()

    async def test_partial_purge_reports_count(
        self,
        purge_cog: Purge,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """When fewer messages deleted than requested (14-day limit), user should be told."""
        # Request 50 but only 20 were young enough to delete
        mock_ctx.channel.purge = AsyncMock(return_value=[MagicMock()] * 20)

        await purge_cog.prefix_purge(mock_ctx, 50)

        mock_ctx.send.assert_called()
        call_text = mock_ctx.send.call_args[0][0]
        assert "20" in call_text
        assert "14 days" in call_text.lower()
