"""Unit tests for the Poll cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from tux.cogs.utility.poll import Poll
from tests.fixtures.dependency_injection import mock_bot_with_container
from prisma.enums import CaseType


@pytest.fixture
def poll_cog(mock_bot_with_container):
    """Create a Poll cog instance with mocked dependencies."""
    return Poll(mock_bot_with_container)


@pytest.mark.asyncio
class TestPollCog:
    """Test cases for the Poll cog."""

    async def test_cog_initialization(self, poll_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert poll_cog.bot is not None
        assert poll_cog.db_service is not None
        assert hasattr(poll_cog, 'db')  # Backward compatibility

    async def test_is_pollbanned_true(self, poll_cog):
        """Test is_pollbanned returns True when user has active poll ban."""
        guild_id = 12345
        user_id = 67890

        # Mock case with POLLBAN type
        mock_case = Mock()
        mock_case.case_type = CaseType.POLLBAN

        poll_cog.db.case.get_latest_case_by_user = AsyncMock(return_value=mock_case)

        result = await poll_cog.is_pollbanned(guild_id, user_id)

        assert result is True
        poll_cog.db.case.get_latest_case_by_user.assert_called_once_with(
            guild_id=guild_id,
            user_id=user_id,
            case_types=[CaseType.POLLBAN, CaseType.POLLUNBAN],
        )

    async def test_is_pollbanned_false_unbanned(self, poll_cog):
        """Test is_pollbanned returns False when user was unbanned."""
        guild_id = 12345
        user_id = 67890

        # Mock case with POLLUNBAN type
        mock_case = Mock()
        mock_case.case_type = CaseType.POLLUNBAN

        poll_cog.db.case.get_latest_case_by_user = AsyncMock(return_value=mock_case)

        result = await poll_cog.is_pollbanned(guild_id, user_id)

        assert result is False

    async def test_is_pollbanned_false_no_cases(self, poll_cog):
        """Test is_pollbanned returns False when user has no relevant cases."""
        guild_id = 12345
        user_id = 67890

        poll_cog.db.case.get_latest_case_by_user = AsyncMock(return_value=None)

        result = await poll_cog.is_pollbanned(guild_id, user_id)

        assert result is False

    async def test_on_message_poll_channel_tux_embed(self, poll_cog):
        """Tesage creates thread for Tux poll with embed."""
        # Mock message in poll channel
        message = Mock()
        message.channel = Mock()
        message.channel.id = 1228717294788673656  # Poll channel ID
        message.author = Mock()
        message.author.id = 12345  # Tux bot ID
        message.author.name = "Tux"
        message.embeds = [Mock()]  # Has embeds
        message.create_thread = AsyncMock()

        # Mock bot user
        poll_cog.bot.user = Mock()
        poll_cog.bot.user.id = 12345
        poll_cog.bot.get_channel = Mock(return_value=message.channel)

        await poll_cog.on_message(message)

        message.create_thread.assert_called_once_with(name="Poll by Tux")

    async def test_on_message_poll_channel_discord_poll(self, poll_cog):
        """Test on_message creates thread for Discord native poll."""
        # Mock message in poll channel
        message = Mock()
        message.channel = Mock()
        message.channel.id = 1228717294788673656  # Poll channel ID
        message.author = Mock()
        message.author.id = 67890  # Not Tux
        message.author.name = "User"
        message.embeds = []
        message.poll = Mock()  # Has Discord poll
        message.create_thread = AsyncMock()

        poll_cog.bot.user = Mock()
        poll_cog.bot.user.id = 12345
        poll_cog.bot.get_channel = Mock(return_value=message.channel)

        await poll_cog.on_message(message)

        message.create_thread.assert_called_once_with(name="Poll by User")

    async def test_on_message_poll_channel_delete_invalid(self, poll_cog):
        """Test on_message deletes invalid messages in poll channel."""
        # Mock message in poll channel without poll or embed
        message = Mock()
        message.channel = Mock()
        message.channel.id = 1228717294788673656  # Poll channel ID
        message.author = Mock()
        message.author.id = 67890  # Not Tux
        message.embeds = []
        message.poll = None
        message.delete = AsyncMock()

        poll_cog.bot.user = Mock()
        poll_cog.bot.user.id = 12345
        poll_cog.bot.get_channel = Mock(return_value=message.channel)
        poll_cog.bot.process_commands = AsyncMock()

        await poll_cog.on_message(message)

        message.delete.assert_called_once()
        poll_cog.bot.process_commands.assert_called_once_with(message)

    async def test_on_message_non_poll_channel(self, poll_cog):
        """Test on_message ignores messages in non-poll channels."""
        # Mock message in different channel
        message = Mock()
        message.channel = Mock()
        message.channel.id = 999999  # Different channel

        poll_cog.bot.get_channel = Mock(return_value=Mock())

        await poll_cog.on_message(message)

        # Should not process the message at all
        assert not hasattr(message, 'delete') or not message.delete.called

    async def test_poll_command_success(self, poll_cog):
        """Test successful poll creation."""
        # Mock interaction
        interaction = Mock()
        interaction.guild_id = 12345
        interaction.user = Mock()
        interaction.user.id = 67890
        interaction.user.name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "http://example.com/avatar.png"
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()
        interaction.original_response = AsyncMock()

        # Mock message for adding reactions
        mock_message = Mock()
        mock_message.add_reaction = AsyncMock()
        interaction.original_response.return_value = mock_message

        # Mock is_pollbanned to return False
        poll_cog.is_pollbanned = AsyncMock(return_value=False)

        title = "Test Poll"
        options = "Option 1, Option 2, Option 3"

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await poll_cog.poll(interaction, title, options)

            # Verify poll was created
            interaction.response.send_message.assert_called_once_with(embed=mock_embed)

            # Verify reactions were added
            assert mock_message.add_reaction.call_count == 3
            mock_message.add_reaction.assert_any_call("1⃣")
            mock_message.add_reaction.assert_any_call("2⃣")
            mock_message.add_reaction.assert_any_call("3⃣")

    async def test_poll_command_pollbanned(self, poll_cog):
        """Test poll command when user is poll banned."""
        # Mock interaction
        interaction = Mock()
        interaction.guild_id = 12345
        interaction.user = Mock()
        interaction.user.id = 67890
        interaction.user.name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "http://example.com/avatar.png"
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()

        # Mock is_pollbanned to return True
        poll_cog.is_pollbanned = AsyncMock(return_value=True)

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await poll_cog.poll(interaction, "Test", "Option 1, Option 2")

            # Verify error response
            interaction.response.send_message.assert_called_once_with(embed=mock_embed, ephemeral=True)

            # Verify embed was created with error type
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert call_args['title'] == "Poll Banned"

    async def test_poll_command_invalid_options_count(self, poll_cog):
        """Test poll command with invalid number of options."""
        # Mock interaction
        interaction = Mock()
        interaction.guild_id = 12345
        interaction.user = Mock()
        interaction.user.id = 67890
        interaction.user.name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "http://example.com/avatar.png"
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()

        # Mock is_pollbanned to return False
        poll_cog.is_pollbanned = AsyncMock(return_value=False)

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            # Test with only one option
            await poll_cog.poll(interaction, "Test", "Only one option")

            # Verify error response
            interaction.response.send_message.assert_called_once_with(
                embed=mock_embed, ephemeral=True, delete_after=30,
            )

            # Verify embed was created with error type
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert call_args['title'] == "Invalid options count"

    async def test_poll_command_no_guild(self, poll_cog):
        """Test poll command when not in a guild."""
        # Mock interaction without guild
        interaction = Mock()
        interaction.guild_id = None
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()

        await poll_cog.poll(interaction, "Test", "Option 1, Option 2")

        interaction.response.send_message.assert_called_once_with(
            "This command can only be used in a server.", ephemeral=True,
        )

    async def test_on_raw_reaction_add_clear_invalid_reaction(self, poll_cog):
        """Test clearing invalid reactions on poll embeds."""
        # Mock payload
        payload = Mock()
        payload.channel_id = 12345
        payload.message_id = 67890
        payload.emoji = Mock()
        payload.emoji.id = None  # Unicode emoji
        payload.emoji.name = "❤️"  # Invalid for polls

        # Mock channel and message
        mock_channel = Mock()
        mock_message = Mock()
        mock_message.embeds = [Mock()]
        mock_message.reactions = []

        # Mock embed with poll author
        mock_embed = Mock()
        mock_embed.author = Mock()
        mock_embed.author.name = "Poll by TestUser"
        mock_message.embeds = [mock_embed]

        # Mock reaction
        mock_reaction = Mock()
        mock_reaction.message = mock_message
        mock_reaction.emoji = "❤️"
        mock_reaction.clear = AsyncMock()
        mock_message.reactions = [mock_reaction]

        mock_channel.fetch_message = AsyncMock(return_value=mock_message)

        with patch('tux.utils.converters.get_channel_safe', return_value=mock_channel):
            with patch('discord.utils.get', return_value=mock_reaction):
                await poll_cog.on_raw_reaction_add(payload)

                # Verify invalid reaction was cleared
                mock_reaction.clear.assert_called_once()

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        cog = Poll(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, poll_cog):
        """Test the string representation of the cog."""
        repr_str = repr(poll_cog)
        assert "Poll" in repr_str
        assert "injection=" in repr_str
