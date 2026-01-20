"""Tests for utility functions."""

from datetime import UTC, datetime

from tux.plugins.v0_1_db_migrate.utils import (
    convert_prisma_to_sqlmodel_name,
    normalize_datetime,
    safe_json_parse,
    transform_enum_value,
)


class TestUtils:
    """Test utility functions."""

    def test_convert_prisma_to_sqlmodel_name(self) -> None:
        """Test Prisma to SQLModel name conversion."""
        assert convert_prisma_to_sqlmodel_name("guildId") == "guild_id"
        assert convert_prisma_to_sqlmodel_name("caseType") == "case_type"
        assert convert_prisma_to_sqlmodel_name("Guild") == "guild"
        assert convert_prisma_to_sqlmodel_name("GuildConfig") == "guild_config"

    def test_transform_enum_value(self) -> None:
        """Test enum value transformation."""
        mapping = {"BAN": "BAN", "KICK": "KICK"}

        assert transform_enum_value("BAN", mapping) == "BAN"
        assert transform_enum_value("KICK", mapping) == "KICK"
        assert transform_enum_value("UNKNOWN", mapping, "BAN") == "BAN"
        assert transform_enum_value(None, mapping, "BAN") == "BAN"

    def test_normalize_datetime(self) -> None:
        """Test datetime normalization."""
        # Test with timezone-aware datetime
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        normalized = normalize_datetime(dt)
        assert normalized is not None
        assert normalized.year == 2024

        # Test with naive datetime
        dt_naive = datetime(2024, 1, 1, 0, 0, 0)  # noqa: DTZ001
        normalized = normalize_datetime(dt_naive)
        assert normalized is not None

        # Test with None
        assert normalize_datetime(None) is None

        # Test with ISO string
        normalized = normalize_datetime("2024-01-01T00:00:00Z")
        assert normalized is not None
        assert normalized.year == 2024

    def test_safe_json_parse(self) -> None:
        """Test JSON parsing."""
        # Test with dict
        assert safe_json_parse({"key": "value"}) == {"key": "value"}

        # Test with list
        assert safe_json_parse([1, 2, 3]) == [1, 2, 3]

        # Test with JSON string
        assert safe_json_parse('{"key": "value"}') == {"key": "value"}

        # Test with None
        assert safe_json_parse(None) is None

        # Test with invalid JSON
        result = safe_json_parse("invalid json")
        assert result is None
