"""Shared fixtures for Sentry and Discord testing."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
from discord.ext import commands

from tux.core.bot import Tux


@pytest.fixture
def mock_sentry_sdk():
    """Mock sentry_sdk for testing."""
    with patch("tux.services.sentry.sentry_sdk") as mock_sdk:
        mock_sdk.is_initialized.return_value = True
        mock_scope = MagicMock()
        mock_sdk.configure_scope.return_value.__enter__.return_value = mock_scope
        mock_sdk.configure_scope.return_value.__exit__.return_value = None
        yield mock_sdk


# Discord User/Member Fixtures


@pytest.fixture
def mock_discord_user():
    """Create mock Discord user."""
    user = MagicMock(spec=discord.User)
    user.id = 123456789
    user.name = "testuser"
    user.discriminator = "1234"
    user.display_name = "Test User"
    user.bot = False
    user.mention = "<@123456789>"
    return user


@pytest.fixture
def mock_discord_member(mock_discord_user):
    """Create mock Discord member."""
    member = MagicMock(spec=discord.Member)
    # Copy user attributes
    for attr in ['id', 'name', 'discriminator', 'display_name', 'bot', 'mention']:
        setattr(member, attr, getattr(mock_discord_user, attr))

    # Add member-specific attributes
    member.guild_permissions = MagicMock()
    member.guild_permissions.administrator = False
    member.guild_permissions.manage_messages = True
    member.roles = []
    member.top_role = MagicMock()
    member.top_role.position = 1
    return member


@pytest.fixture
def mock_discord_guild():
    """Create mock Discord guild."""
    guild = MagicMock(spec=discord.Guild)
    guild.id = 987654321
    guild.name = "Test Guild"
    guild.member_count = 100
    guild.owner_id = 111222333
    return guild


@pytest.fixture
def mock_discord_channel():
    """Create mock Discord channel."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 555666777
    channel.name = "test-channel"
    channel.mention = "<#555666777>"
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_discord_interaction(mock_discord_user, mock_discord_guild, mock_discord_channel):
    """Create mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = mock_discord_user
    interaction.guild = mock_discord_guild
    interaction.guild_id = mock_discord_guild.id
    interaction.channel = mock_discord_channel
    interaction.channel_id = mock_discord_channel.id

    # Mock command
    interaction.command = MagicMock()
    interaction.command.qualified_name = "test_command"

    # Mock response
    interaction.response = MagicMock()
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()

    # Mock followup
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    return interaction


# Discord Context Fixtures
@pytest.fixture
def mock_discord_context(mock_discord_user, mock_discord_guild, mock_discord_channel):
    """Create mock Discord command context."""
    ctx = MagicMock(spec=commands.Context)
    ctx.author = mock_discord_user
    ctx.guild = mock_discord_guild
    ctx.channel = mock_discord_channel
    ctx.message = MagicMock()
    ctx.message.id = 888999000

    # Mock command
    ctx.command = MagicMock()
    ctx.command.qualified_name = "test_command"
    ctx.command.has_error_handler.return_value = False

    # Mock cog
    ctx.cog = None

    # Mock reply method
    ctx.reply = AsyncMock()
    ctx.send = AsyncMock()

    return ctx


# Bot Fixtures
@pytest.fixture
def mock_tux_bot():
    """Create mock Tux bot."""
    bot = MagicMock(spec=Tux)
    bot.user = MagicMock()
    bot.user.id = 999888777
    bot.user.name = "TuxBot"

    # Mock tree for app commands
    bot.tree = MagicMock()
    bot.tree.on_error = MagicMock()

    return bot


# Error Fixtures
@pytest.fixture
def mock_command_error():
    """Create mock command error."""
    return commands.CommandError("Test command error")


@pytest.fixture
def mock_app_command_error():
    """Create mock app command error."""
    return discord.app_commands.AppCommandError("Test app command error")


# Sentry Tracking Fixtures
@pytest.fixture
def sentry_capture_calls():
    """Track Sentry capture calls for assertions."""
    calls = []

    def capture_side_effect(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})

    with patch("tux.services.sentry.capture_exception_safe", side_effect=capture_side_effect) as mock_capture:
        yield {"calls": calls, "mock": mock_capture}


@pytest.fixture
def sentry_context_calls():
    """Track Sentry context calls for assertions."""
    calls = {"set_context": [], "set_tag": [], "set_user": []}

    def set_context_side_effect(*args, **kwargs):
        calls["set_context"].append({"args": args, "kwargs": kwargs})

    def set_tag_side_effect(*args, **kwargs):
        calls["set_tag"].append({"args": args, "kwargs": kwargs})

    def set_user_side_effect(*args, **kwargs):
        calls["set_user"].append({"args": args, "kwargs": kwargs})

    with patch("tux.services.sentry.set_context", side_effect=set_context_side_effect), \
         patch("tux.services.sentry.set_tag", side_effect=set_tag_side_effect), \
         patch("tux.services.sentry.set_user_context") as mock_set_user:

        mock_set_user.side_effect = set_user_side_effect
        yield calls
