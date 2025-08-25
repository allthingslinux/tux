"""
Unit tests for database models.

Tests model validation, relationships, constraints, and basic functionality.
"""

import pytest
from datetime import datetime, UTC
from pydantic import ValidationError

from tux.database.models import (
    Guild, GuildConfig, Snippet, Reminder, Case, CaseType,
    Note, GuildPermission, PermissionType, AccessType, AFK, Levels,
    Starboard, StarboardMessage,
)
from tests.fixtures.database_fixtures import (
    TEST_GUILD_ID, TEST_USER_ID, TEST_CHANNEL_ID, TEST_MESSAGE_ID,
    sample_guild, sample_guild_config, sample_snippet, sample_reminder,
    sample_case, sample_note, sample_guild_permission,
    sample_afk, sample_levels, sample_starboard, sample_starboard_message,
)


class TestGuildModel:
    """Test Guild model functionality."""

    def test_guild_creation(self, sample_guild: Guild):
        """Test basic guild creation."""
        assert sample_guild.guild_id == TEST_GUILD_ID
        assert sample_guild.case_count == 0
        assert sample_guild.guild_joined_at is None  # Auto-set in real usage

    def test_guild_config_relationship(self, sample_guild: Guild, sample_guild_config: GuildConfig):
        """Test guild-config relationship."""
        # This would normally be set by SQLAlchemy relationships
        sample_guild.guild_config = sample_guild_config
        assert sample_guild.guild_config.guild_id == TEST_GUILD_ID
        assert sample_guild.guild_config.prefix == "!"

    def test_guild_constraints(self):
        """Test guild model constraints."""
        # Test valid guild ID
        guild = Guild(guild_id=123456789012345678)
        assert guild.guild_id == 123456789012345678

        # Test case count default
        assert guild.case_count == 0

        # Test case count update
        guild.case_count = 5
        assert guild.case_count == 5


class TestGuildConfigModel:
    """Test GuildConfig model functionality."""

    def test_guild_config_creation(self, sample_guild_config: GuildConfig):
        """Test basic guild config creation."""
        assert sample_guild_config.guild_id == TEST_GUILD_ID
        assert sample_guild_config.prefix == "!"
        assert sample_guild_config.mod_log_id == TEST_CHANNEL_ID

    def test_guild_config_optional_fields(self):
        """Test that optional fields work correctly."""
        config = GuildConfig(guild_id=TEST_GUILD_ID)
        assert config.prefix is None
        assert config.mod_log_id is None
        assert config.audit_log_id is None
        assert config.starboard_channel_id is None

    def test_guild_config_field_lengths(self, sample_guild_config: GuildConfig):
        """Test field length constraints."""
        assert len(sample_guild_config.prefix) <= 10  # prefix max_length=10

    def test_guild_config_relationship(self, sample_guild: Guild, sample_guild_config: GuildConfig):
        """Test guild-config bidirectional relationship."""
        sample_guild_config.guild = sample_guild
        assert sample_guild_config.guild.guild_id == TEST_GUILD_ID


class TestSnippetModel:
    """Test Snippet model functionality."""

    def test_snippet_creation(self, sample_snippet: Snippet):
        """Test basic snippet creation."""
        assert sample_snippet.snippet_name == "test_snippet"
        assert sample_snippet.snippet_content == "This is a test snippet content"
        assert sample_snippet.snippet_user_id == TEST_USER_ID
        assert sample_snippet.guild_id == TEST_GUILD_ID
        assert sample_snippet.uses == 5
        assert sample_snippet.locked is False

    def test_snippet_field_lengths(self):
        """Test snippet field length constraints."""
        # Test snippet name length (max 100)
        snippet = Snippet(
            snippet_name="a" * 100,
            snippet_content="test",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert len(snippet.snippet_name) == 100

        # Test snippet content length (max 4000)
        snippet = Snippet(
            snippet_name="test",
            snippet_content="a" * 4000,
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert len(snippet.snippet_content) == 4000

    def test_snippet_defaults(self):
        """Test snippet default values."""
        snippet = Snippet(
            snippet_name="test",
            snippet_content="content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert snippet.uses == 0
        assert snippet.locked is False
        assert snippet.alias is None

    def test_snippet_constraints(self):
        """Test snippet model constraints."""
        # Test uses counter
        snippet = Snippet(
            snippet_name="test",
            snippet_content="content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
            uses=10,
        )
        assert snippet.uses == 10

        snippet.uses += 1
        assert snippet.uses == 11


class TestReminderModel:
    """Test Reminder model functionality."""

    def test_reminder_creation(self, sample_reminder: Reminder):
        """Test basic reminder creation."""
        assert sample_reminder.reminder_content == "Test reminder"
        assert sample_reminder.reminder_channel_id == TEST_CHANNEL_ID
        assert sample_reminder.reminder_user_id == TEST_USER_ID
        assert sample_reminder.guild_id == TEST_GUILD_ID
        assert sample_reminder.reminder_sent is False

    def test_reminder_field_lengths(self):
        """Test reminder field length constraints."""
        # Test reminder content length (max 2000)
        reminder = Reminder(
            reminder_content="a" * 2000,
            reminder_expires_at=datetime.now(UTC),
            reminder_channel_id=TEST_CHANNEL_ID,
            reminder_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert len(reminder.reminder_content) == 2000

    def test_reminder_sent_flag(self, sample_reminder: Reminder):
        """Test reminder sent flag functionality."""
        assert sample_reminder.reminder_sent is False

        sample_reminder.reminder_sent = True
        assert sample_reminder.reminder_sent is True


class TestCaseModel:
    """Test Case model functionality."""

    def test_case_creation(self, sample_case: Case):
        """Test basic case creation."""
        assert sample_case.case_status is True
        assert sample_case.case_reason == "Test case reason"
        assert sample_case.case_moderator_id == TEST_USER_ID
        assert sample_case.case_user_id == TEST_USER_ID + 1
        assert sample_case.case_user_roles == [TEST_USER_ID + 2, TEST_USER_ID + 3]
        assert sample_case.case_number == 1
        assert sample_case.guild_id == TEST_GUILD_ID

    def test_case_type_enum(self):
        """Test CaseType enum values."""
        assert CaseType.BAN.value == "BAN"
        assert CaseType.KICK.value == "KICK"
        assert CaseType.WARN.value == "WARN"
        assert CaseType.TIMEOUT.value == "TIMEOUT"

    def test_case_optional_fields(self):
        """Test case optional fields."""
        case = Case(
            case_reason="Test",
            case_moderator_id=TEST_USER_ID,
            case_user_id=TEST_USER_ID + 1,
            guild_id=TEST_GUILD_ID,
        )
        assert case.case_type is None
        assert case.case_number is None
        assert case.case_expires_at is None
        assert case.case_metadata is None

    def test_case_user_roles(self):
        """Test case user roles list."""
        case = Case(
            case_reason="Test",
            case_moderator_id=TEST_USER_ID,
            case_user_id=TEST_USER_ID + 1,
            guild_id=TEST_GUILD_ID,
            case_user_roles=[1, 2, 3, 4, 5],
        )
        assert case.case_user_roles == [1, 2, 3, 4, 5]



class TestNoteModel:
    """Test Note model functionality."""

    def test_note_creation(self, sample_note: Note):
        """Test basic note creation."""
        assert sample_note.note_content == "Test note content"
        assert sample_note.note_moderator_id == TEST_USER_ID
        assert sample_note.note_user_id == TEST_USER_ID + 1
        assert sample_note.note_number == 1
        assert sample_note.guild_id == TEST_GUILD_ID

    def test_note_field_lengths(self):
        """Test note field length constraints."""
        # Test note content length (max 2000)
        note = Note(
            note_content="a" * 2000,
            note_moderator_id=TEST_USER_ID,
            note_user_id=TEST_USER_ID + 1,
            note_number=1,
            guild_id=TEST_GUILD_ID,
        )
        assert len(note.note_content) == 2000


class TestGuildPermissionModel:
    """Test GuildPermission model functionality."""

    def test_guild_permission_creation(self, sample_guild_permission: GuildPermission):
        """Test basic guild permission creation."""
        assert sample_guild_permission.id == 1
        assert sample_guild_permission.guild_id == TEST_GUILD_ID
        assert sample_guild_permission.permission_type == PermissionType.MEMBER
        assert sample_guild_permission.access_type == AccessType.WHITELIST
        assert sample_guild_permission.target_id == TEST_USER_ID
        assert sample_guild_permission.is_active is True

    def test_permission_type_enum(self):
        """Test PermissionType enum values."""
        assert PermissionType.MEMBER.value == "member"
        assert PermissionType.CHANNEL.value == "channel"
        assert PermissionType.COMMAND.value == "command"
        assert PermissionType.MODULE.value == "module"

    def test_access_type_enum(self):
        """Test AccessType enum values."""
        assert AccessType.WHITELIST.value == "whitelist"
        assert AccessType.BLACKLIST.value == "blacklist"
        assert AccessType.IGNORE.value == "ignore"

    def test_guild_permission_optional_fields(self):
        """Test guild permission optional fields."""
        perm = GuildPermission(
            id=2,
            guild_id=TEST_GUILD_ID,
            permission_type=PermissionType.COMMAND,
            access_type=AccessType.WHITELIST,
            target_id=TEST_CHANNEL_ID,
        )
        assert perm.target_name is None
        assert perm.command_name is None
        assert perm.module_name is None
        assert perm.expires_at is None
        assert perm.is_active is True  # Default value


class TestAFKModel:
    """Test AFK model functionality."""

    def test_afk_creation(self, sample_afk: AFK):
        """Test basic AFK creation."""
        assert sample_afk.member_id == TEST_USER_ID
        assert sample_afk.nickname == "TestUser"
        assert sample_afk.reason == "Testing AFK functionality"
        assert sample_afk.guild_id == TEST_GUILD_ID
        assert sample_afk.enforced is False
        assert sample_afk.perm_afk is False

    def test_afk_field_lengths(self):
        """Test AFK field length constraints."""
        # Test nickname length (max 100)
        afk = AFK(
            member_id=TEST_USER_ID,
            nickname="a" * 100,
            reason="Test",
            guild_id=TEST_GUILD_ID,
        )
        assert len(afk.nickname) == 100

        # Test reason length (max 500)
        afk = AFK(
            member_id=TEST_USER_ID,
            nickname="test",
            reason="a" * 500,
            guild_id=TEST_GUILD_ID,
        )
        assert len(afk.reason) == 500

    def test_afk_defaults(self, sample_afk: AFK):
        """Test AFK default values."""
        assert sample_afk.until is None
        assert sample_afk.enforced is False
        assert sample_afk.perm_afk is False


class TestLevelsModel:
    """Test Levels model functionality."""

    def test_levels_creation(self, sample_levels: Levels):
        """Test basic levels creation."""
        assert sample_levels.member_id == TEST_USER_ID
        assert sample_levels.guild_id == TEST_GUILD_ID
        assert sample_levels.xp == 150.5
        assert sample_levels.level == 3
        assert sample_levels.blacklisted is False

    def test_levels_defaults(self):
        """Test levels default values."""
        levels = Levels(
            member_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert levels.xp == 0.0
        assert levels.level == 0
        assert levels.blacklisted is False

    def test_levels_xp_operations(self, sample_levels: Levels):
        """Test XP operations."""
        original_xp = sample_levels.xp

        sample_levels.xp += 25.5
        assert sample_levels.xp == original_xp + 25.5

        sample_levels.level += 1
        assert sample_levels.level == 4


class TestStarboardModel:
    """Test Starboard model functionality."""

    def test_starboard_creation(self, sample_starboard: Starboard):
        """Test basic starboard creation."""
        assert sample_starboard.guild_id == TEST_GUILD_ID
        assert sample_starboard.starboard_channel_id == TEST_CHANNEL_ID
        assert sample_starboard.starboard_emoji == "⭐"
        assert sample_starboard.starboard_threshold == 3

    def test_starboard_defaults(self):
        """Test starboard default values."""
        starboard = Starboard(
            guild_id=TEST_GUILD_ID,
            starboard_channel_id=TEST_CHANNEL_ID,
            starboard_emoji="⭐",
        )
        assert starboard.starboard_threshold == 1

    def test_starboard_field_lengths(self, sample_starboard: Starboard):
        """Test starboard field length constraints."""
        # Test emoji length (max 64)
        starboard = Starboard(
            guild_id=TEST_GUILD_ID,
            starboard_channel_id=TEST_CHANNEL_ID,
            starboard_emoji="a" * 64,
        )
        assert len(starboard.starboard_emoji) == 64


class TestStarboardMessageModel:
    """Test StarboardMessage model functionality."""

    def test_starboard_message_creation(self, sample_starboard_message: StarboardMessage):
        """Test basic starboard message creation."""
        assert sample_starboard_message.message_id == TEST_MESSAGE_ID
        assert sample_starboard_message.message_content == "This is a test message for starboard"
        assert sample_starboard_message.message_channel_id == TEST_CHANNEL_ID + 1
        assert sample_starboard_message.message_user_id == TEST_USER_ID
        assert sample_starboard_message.message_guild_id == TEST_GUILD_ID
        assert sample_starboard_message.star_count == 5
        assert sample_starboard_message.starboard_message_id == TEST_MESSAGE_ID + 1

    def test_starboard_message_field_lengths(self):
        """Test starboard message field length constraints."""
        # Test message content length (max 4000)
        message = StarboardMessage(
            message_id=TEST_MESSAGE_ID,
            message_content="a" * 4000,
            message_expires_at=datetime.now(UTC),
            message_channel_id=TEST_CHANNEL_ID,
            message_user_id=TEST_USER_ID,
            message_guild_id=TEST_GUILD_ID,
            star_count=1,
            starboard_message_id=TEST_MESSAGE_ID + 1,
        )
        assert len(message.message_content) == 4000


class TestModelRelationships:
    """Test relationships between models."""

    def test_guild_guildconfig_relationship(self, sample_guild: Guild, sample_guild_config: GuildConfig):
        """Test Guild-GuildConfig relationship."""
        # Set up relationship
        sample_guild.guild_config = sample_guild_config
        sample_guild_config.guild = sample_guild

        # Test bidirectional relationship
        assert sample_guild.guild_config.guild_id == sample_guild.guild_id
        assert sample_guild_config.guild.guild_id == sample_guild.guild_id

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are properly defined."""
        # These tests verify that the foreign key fields exist and are properly typed

        # Guild references
        guild_config = GuildConfig(guild_id=TEST_GUILD_ID)
        assert hasattr(guild_config, 'guild_id')

        snippet = Snippet(
            snippet_name="test",
            snippet_content="content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert hasattr(snippet, 'guild_id')

        case = Case(
            case_reason="test",
            case_moderator_id=TEST_USER_ID,
            case_user_id=TEST_USER_ID + 1,
            guild_id=TEST_GUILD_ID,
        )
        assert hasattr(case, 'guild_id')


class TestModelValidation:
    """Test model validation and edge cases."""

    def test_required_fields(self):
        """Test that required fields cannot be None for non-optional fields."""
        # These should work (all required fields provided)
        guild = Guild(guild_id=TEST_GUILD_ID)
        assert guild.guild_id is not None

        snippet = Snippet(
            snippet_name="test",
            snippet_content="content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert snippet.snippet_name is not None

    def test_field_types(self):
        """Test that fields have correct types."""
        guild = Guild(guild_id=TEST_GUILD_ID)
        assert isinstance(guild.guild_id, int)
        assert isinstance(guild.case_count, int)

        snippet = Snippet(
            snippet_name="test",
            snippet_content="content",
            snippet_user_id=TEST_USER_ID,
            guild_id=TEST_GUILD_ID,
        )
        assert isinstance(snippet.snippet_name, str)
        assert isinstance(snippet.uses, int)
        assert isinstance(snippet.locked, bool)

    def test_enum_values(self):
        """Test that enum fields work correctly."""
        permission = GuildPermission(
            id=1,
            guild_id=TEST_GUILD_ID,
            permission_type=PermissionType.MEMBER,
            access_type=AccessType.WHITELIST,
            target_id=TEST_USER_ID,
        )

        assert permission.permission_type == PermissionType.MEMBER
        assert permission.access_type == AccessType.WHITELIST
        assert permission.permission_type.value == "member"
        assert permission.access_type.value == "whitelist"
