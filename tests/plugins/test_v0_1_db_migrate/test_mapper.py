"""Tests for model mapper."""

from datetime import datetime

import pytest

from tux.database.models import AFK, Case, Guild, GuildConfig
from tux.plugins.v0_1_db_migrate.mapper import (
    ModelMapper,
)


class TestModelMapper:
    """Test ModelMapper class."""

    @pytest.fixture
    def mapper(self) -> ModelMapper:
        """Create test mapper."""
        return ModelMapper()

    def test_get_table_mapping(self, mapper: ModelMapper) -> None:
        """Test table name mapping."""
        assert mapper.get_table_mapping("Guild") == "guild"
        assert mapper.get_table_mapping("Case") == "cases"
        assert mapper.get_table_mapping("GuildConfig") == "guild_config"
        assert mapper.get_table_mapping("AFKModel") == "afk"
        assert mapper.get_table_mapping("Levels") == "levels"

    def test_get_table_mapping_invalid(self, mapper: ModelMapper) -> None:
        """Test table mapping with invalid name."""
        # Should convert using name conversion
        result = mapper.get_table_mapping("InvalidTable")
        assert isinstance(result, str)

    def test_get_field_mapping(self, mapper: ModelMapper) -> None:
        """Test field name mapping."""
        # Test mapped fields
        assert mapper.get_field_mapping("Guild", "guild_id") == "id"
        assert mapper.get_field_mapping("Case", "case_id") == "id"
        assert (
            mapper.get_field_mapping("Case", "case_tempban_expired") == "case_processed"
        )
        assert (
            mapper.get_field_mapping("StarboardMessage", "message_guild_id")
            == "message_guild_id"
        )

        # Test unmapped fields (should use same name)
        assert mapper.get_field_mapping("Guild", "guild_joined_at") == "guild_joined_at"
        assert mapper.get_field_mapping("Case", "case_reason") == "case_reason"

    def test_transform_row_guild(self, mapper: ModelMapper) -> None:
        """Test transforming Guild row."""
        old_row = {
            "guild_id": 123456789,
            "guild_joined_at": "2024-01-01T00:00:00Z",
            "case_count": 5,
        }
        transformed = mapper.transform_row("Guild", old_row)
        assert transformed["id"] == 123456789
        assert "guild_joined_at" in transformed
        assert transformed["case_count"] == 5

    def test_transform_row_case(self, mapper: ModelMapper) -> None:
        """Test transforming Case row."""
        old_row = {
            "case_id": 1,
            "case_status": True,
            "case_type": "BAN",
            "case_reason": "Test reason",
            "case_moderator_id": 111,
            "case_user_id": 222,
            "case_user_roles": [333, 444],
            "case_number": 1,
            "case_expires_at": None,
            "case_tempban_expired": False,
            "guild_id": 123456789,
            "case_created_at": "2024-01-01T00:00:00Z",
        }
        transformed = mapper.transform_row("Case", old_row)
        assert transformed["id"] == 1
        assert (
            transformed["case_processed"] is False
        )  # Mapped from case_tempban_expired
        assert transformed["case_type"] == "BAN"
        assert "case_tempban_expired" not in transformed

    def test_transform_row_skips_deprecated_fields(self, mapper: ModelMapper) -> None:
        """Test that deprecated fields are skipped."""
        old_row = {
            "guild_id": 123456789,
            "prefix": "$",
            "base_member_role_id": 999,  # Deprecated
            "base_staff_role_id": 888,  # Deprecated
            "general_channel_id": 777,  # Deprecated
        }
        transformed = mapper.transform_row("GuildConfig", old_row)
        assert "base_member_role_id" not in transformed
        assert "base_staff_role_id" not in transformed
        assert "general_channel_id" not in transformed
        assert transformed["id"] == 123456789
        assert transformed["prefix"] == "$"

    def test_transform_row_skips_none_values(self, mapper: ModelMapper) -> None:
        """Test that None values are skipped."""
        old_row = {
            "guild_id": 123456789,
            "prefix": None,
            "mod_log_id": None,
        }
        transformed = mapper.transform_row("GuildConfig", old_row)
        # None values should be skipped (will use defaults)
        assert "prefix" not in transformed or transformed["prefix"] is not None
        assert transformed["id"] == 123456789

    def test_transform_row_afk_model(self, mapper: ModelMapper) -> None:
        """Test transforming AFKModel row."""
        old_row = {
            "member_id": 111111111,
            "guild_id": 123456789,
            "nickname": "TestUser",
            "reason": "AFK reason",
            "since": "2024-01-01T00:00:00Z",
            "until": None,
            "enforced": False,
            "perm_afk": False,
        }
        transformed = mapper.transform_row("AFKModel", old_row)
        assert transformed["member_id"] == 111111111
        assert transformed["guild_id"] == 123456789
        assert transformed["nickname"] == "TestUser"

    def test_transform_row_starboard_message(self, mapper: ModelMapper) -> None:
        """Test transforming StarboardMessage row."""
        old_row = {
            "message_id": 999999999,
            "message_content": "Test content",
            "message_expires_at": None,
            "message_channel_id": 888888888,
            "message_user_id": 777777777,
            "message_guild_id": 123456789,  # Kept as message_guild_id (FK to guild.id)
            "star_count": 5,
            "starboard_message_id": 666666666,
            "message_created_at": "2024-01-01T00:00:00Z",
        }
        transformed = mapper.transform_row("StarboardMessage", old_row)
        assert transformed["id"] == 999999999
        assert transformed["message_guild_id"] == 123456789
        assert transformed["message_content"] == "Test content"

    def test_get_model_class(self, mapper: ModelMapper) -> None:
        """Test model class retrieval."""
        assert mapper.get_model_class("guild") == Guild
        assert mapper.get_model_class("cases") == Case
        assert mapper.get_model_class("guild_config") == GuildConfig
        assert mapper.get_model_class("afk") == AFK

    def test_get_model_class_invalid(self, mapper: ModelMapper) -> None:
        """Test model class retrieval with invalid table name."""
        with pytest.raises(ValueError, match="Unknown table name"):
            mapper.get_model_class("invalid_table")

    def test_transform_row_enum_handling(self, mapper: ModelMapper) -> None:
        """Test enum value transformation."""
        old_row = {
            "case_id": 1,
            "case_type": "BAN",  # Enum value
            "case_reason": "Test",
            "case_moderator_id": 111,
            "case_user_id": 222,
            "guild_id": 123456789,
        }
        transformed = mapper.transform_row("Case", old_row)
        # Enum should be transformed correctly
        assert transformed["case_type"] == "BAN"

    def test_transform_row_datetime_handling(self, mapper: ModelMapper) -> None:
        """Test datetime value transformation."""
        old_row = {
            "guild_id": 123456789,
            "guild_joined_at": "2024-01-01T00:00:00Z",
        }
        transformed = mapper.transform_row("Guild", old_row)
        # Datetime should be normalized
        assert "guild_joined_at" in transformed
        assert isinstance(transformed["guild_joined_at"], (datetime, str))

    def test_transform_row_json_handling(self, mapper: ModelMapper) -> None:
        """Test JSON array handling."""
        old_row = {
            "case_id": 1,
            "case_type": "BAN",
            "case_reason": "Test",
            "case_moderator_id": 111,
            "case_user_id": 222,
            "case_user_roles": [333, 444, 555],  # JSON array
            "guild_id": 123456789,
        }
        transformed = mapper.transform_row("Case", old_row)
        assert transformed["case_user_roles"] == [333, 444, 555]
