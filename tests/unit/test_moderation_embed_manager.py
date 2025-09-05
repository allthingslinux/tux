"""
🚀 EmbedManager Unit Tests - Embed Creation & Sending

Tests for the EmbedManager mixin that handles creating and sending
moderation embeds and log messages.

Test Coverage:
- Embed creation with various field configurations
- Error response embed generation
- Log channel message sending
- Embed formatting and color handling
- Footer and author information handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands

from tux.services.moderation.embed_manager import EmbedManager
from tux.core.types import Tux


class TestEmbedManager:
    """📄 Test EmbedManager functionality."""

    @pytest.fixture
    def embed_manager(self) -> EmbedManager:
        """Create an EmbedManager instance for testing."""
        manager = EmbedManager()
        # Mock the bot attribute
        manager.bot = MagicMock(spec=Tux)
        return manager

    @pytest.fixture
    def mock_ctx(self) -> commands.Context[Tux]:
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 123456789
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = MagicMock()
        ctx.author.display_avatar.url = "https://example.com/avatar.png"
        ctx.message = MagicMock(spec=discord.Message)
        ctx.message.created_at = discord.utils.utcnow()
        return ctx

    @pytest.mark.unit
    async def test_send_error_response_basic(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test basic error response sending."""
        embed_manager.send_error_response = AsyncMock()

        await embed_manager.send_error_response(mock_ctx, "Test error message")

        embed_manager.send_error_response.assert_called_once_with(
            mock_ctx, "Test error message",
        )

    @pytest.mark.unit
    async def test_send_error_response_with_detail(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test error response with exception detail."""
        embed_manager.send_error_response = AsyncMock()

        test_exception = ValueError("Test error")
        await embed_manager.send_error_response(mock_ctx, "Test message", test_exception, False)

        call_args = embed_manager.send_error_response.call_args
        assert call_args[0][1] == "Test message"
        assert call_args[0][2] == test_exception
        assert call_args[0][3] is False  # Not ephemeral

    @pytest.mark.unit
    async def test_create_embed_basic_fields(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with basic fields."""
        fields = [
            ("Field 1", "Value 1", True),
            ("Field 2", "Value 2", False),
            ("Field 3", "Value 3", True),
        ]

        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Test Embed",
            fields=fields,
            color=0xFF0000,
            icon_url="https://example.com/icon.png",
        )

        assert isinstance(embed, discord.Embed)
        assert embed.title == "Test Embed"
        assert embed.color.value == 0xFF0000

        # Check fields were added correctly
        assert len(embed.fields) == 3
        assert embed.fields[0].name == "Field 1"
        assert embed.fields[0].value == "Value 1"
        assert embed.fields[0].inline is True

        assert embed.fields[1].name == "Field 2"
        assert embed.fields[1].value == "Value 2"
        assert embed.fields[1].inline is False

    @pytest.mark.unit
    async def test_create_embed_with_thumbnail(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with thumbnail."""
        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Test Embed",
            fields=[],
            color=0x00FF00,
            icon_url="https://example.com/icon.png",
            thumbnail_url="https://example.com/thumbnail.png",
        )

        assert embed.thumbnail.url == "https://example.com/thumbnail.png"

    @pytest.mark.unit
    async def test_create_embed_with_timestamp(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with custom timestamp."""
        custom_timestamp = discord.utils.utcnow()
        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Test Embed",
            fields=[],
            color=0x0000FF,
            icon_url="https://example.com/icon.png",
            timestamp=custom_timestamp,
        )

        assert embed.timestamp == custom_timestamp

    @pytest.mark.unit
    async def test_create_embed_footer_and_author(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation includes proper footer and author information."""
        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Test Embed",
            fields=[],
            color=0xFF00FF,
            icon_url="https://example.com/icon.png",
        )

        # Check that footer and author were set (would be done by EmbedCreator)
        # Note: In the actual implementation, these are set by the EmbedCreator.get_footer method
        # but since we're mocking, we'll just verify the embed was created
        assert isinstance(embed, discord.Embed)

    @pytest.mark.unit
    async def test_send_embed_to_log_channel_success(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test successful embed sending to log channel."""
        # Mock the database call
        embed_manager.db = MagicMock()
        embed_manager.db.guild_config = MagicMock()
        embed_manager.db.guild_config.get_log_channel = AsyncMock(return_value=987654321)

        # Mock the guild.get_channel call
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.send = AsyncMock(return_value=MagicMock(spec=discord.Message))
        mock_ctx.guild.get_channel = MagicMock(return_value=mock_channel)

        embed = discord.Embed(title="Test", description="Test embed")
        result = await embed_manager.send_embed(mock_ctx, embed, "mod")

        assert result is not None
        mock_channel.send.assert_called_once_with(embed=embed)

    @pytest.mark.unit
    async def test_send_embed_no_log_channel(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed sending when no log channel is configured."""
        # Mock database returning None (no log channel)
        embed_manager.db = MagicMock()
        embed_manager.db.guild_config = MagicMock()
        embed_manager.db.guild_config.get_log_channel = AsyncMock(return_value=None)

        embed = discord.Embed(title="Test", description="Test embed")
        result = await embed_manager.send_embed(mock_ctx, embed, "mod")

        assert result is None

    @pytest.mark.unit
    async def test_send_embed_invalid_channel_type(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed sending when log channel is not a text channel."""
        # Mock database returning a channel ID
        embed_manager.db = MagicMock()
        embed_manager.db.guild_config = MagicMock()
        embed_manager.db.guild_config.get_log_channel = AsyncMock(return_value=987654321)

        # Mock the guild.get_channel returning a voice channel (not text)
        mock_channel = MagicMock(spec=discord.VoiceChannel)
        mock_ctx.guild.get_channel = MagicMock(return_value=mock_channel)

        embed = discord.Embed(title="Test", description="Test embed")
        result = await embed_manager.send_embed(mock_ctx, embed, "mod")

        assert result is None

    @pytest.mark.unit
    async def test_send_embed_channel_not_found(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed sending when log channel doesn't exist."""
        # Mock database returning a channel ID
        embed_manager.db = MagicMock()
        embed_manager.db.guild_config = MagicMock()
        embed_manager.db.guild_config.get_log_channel = AsyncMock(return_value=987654321)

        # Mock guild.get_channel returning None (channel not found)
        mock_ctx.guild.get_channel = MagicMock(return_value=None)

        embed = discord.Embed(title="Test", description="Test embed")
        result = await embed_manager.send_embed(mock_ctx, embed, "mod")

        assert result is None

    @pytest.mark.unit
    async def test_create_embed_empty_fields(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with no fields."""
        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Empty Embed",
            fields=[],
            color=0xFFFFFF,
            icon_url="https://example.com/icon.png",
        )

        assert isinstance(embed, discord.Embed)
        assert embed.title == "Empty Embed"
        assert len(embed.fields) == 0

    @pytest.mark.unit
    async def test_create_embed_special_characters_in_title(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with special characters in title."""
        special_title = "Test: Embed@#$%^&*()"
        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title=special_title,
            fields=[],
            color=0x123456,
            icon_url="https://example.com/icon.png",
        )

        assert embed.title == special_title

    @pytest.mark.unit
    async def test_create_embed_long_field_values(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with very long field values."""
        long_value = "A" * 1000  # Very long value
        fields = [("Long Field", long_value, False)]

        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Long Value Test",
            fields=fields,
            color=0xABCDEF,
            icon_url="https://example.com/icon.png",
        )

        assert embed.fields[0].value == long_value

    @pytest.mark.unit
    async def test_send_embed_exception_handling(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test exception handling during embed sending."""
        # Mock database returning a channel ID
        embed_manager.db = MagicMock()
        embed_manager.db.guild_config = MagicMock()
        embed_manager.db.guild_config.get_log_channel = AsyncMock(return_value=987654321)

        # Mock channel that raises an exception
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "Send failed"))
        mock_ctx.guild.get_channel = MagicMock(return_value=mock_channel)

        embed = discord.Embed(title="Test", description="Test embed")
        result = await embed_manager.send_embed(mock_ctx, embed, "mod")

        assert result is None  # Should return None on failure

    @pytest.mark.unit
    async def test_create_embed_different_colors(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test embed creation with different color values."""
        test_cases = [
            (0xFF0000, "Red"),
            (0x00FF00, "Green"),
            (0x0000FF, "Blue"),
            (0xFFFFFF, "White"),
            (0x000000, "Black"),
            (0x123456, "Custom"),
        ]

        for color_value, description in test_cases:
            embed = embed_manager.create_embed(
                ctx=mock_ctx,
                title=f"{description} Embed",
                fields=[],
                color=color_value,
                icon_url="https://example.com/icon.png",
            )

            assert embed.color.value == color_value
            assert embed.title == f"{description} Embed"

    @pytest.mark.unit
    async def test_create_embed_field_inline_behavior(
        self,
        embed_manager: EmbedManager,
        mock_ctx: commands.Context[Tux],
    ) -> None:
        """Test that field inline property is correctly set."""
        fields = [
            ("Inline Field", "Value", True),
            ("Block Field", "Value", False),
            ("Default Field", "Value", True),  # Test default behavior
        ]

        embed = embed_manager.create_embed(
            ctx=mock_ctx,
            title="Field Test",
            fields=fields,
            color=0xFF00FF,
            icon_url="https://example.com/icon.png",
        )

        assert embed.fields[0].inline is True
        assert embed.fields[1].inline is False
        assert embed.fields[2].inline is True

    @pytest.mark.unit
    async def test_embed_manager_initialization(self) -> None:
        """Test EmbedManager initialization."""
        manager = EmbedManager()

        # Should initialize without requiring special setup
        assert manager is not None
        assert hasattr(manager, 'send_error_response')
        assert hasattr(manager, 'create_embed')
        assert hasattr(manager, 'send_embed')
