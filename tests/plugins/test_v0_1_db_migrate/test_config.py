"""Tests for migration configuration."""

import os
from unittest.mock import patch

from tux.plugins.v0_1_db_migrate.config import (
    MigrationConfig,
    get_old_database_url,
)


class TestGetOldDatabaseUrl:
    """Test get_old_database_url function."""

    def test_get_url_from_env(self) -> None:
        """Test getting URL from environment variable."""
        test_url = "postgresql+psycopg://user:pass@host:5432/db"
        with patch.dict(os.environ, {"OLD_DATABASE_URL": test_url}):
            result = get_old_database_url()
            assert result == test_url

    def test_get_url_empty_when_env_unset(self) -> None:
        """Test getting empty string when OLD_DATABASE_URL not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_old_database_url()
            assert result == ""

    def test_convert_postgres_to_postgresql(self) -> None:
        """Test conversion of postgres:// to postgresql+psycopg://."""
        with patch.dict(
            os.environ,
            {"OLD_DATABASE_URL": "postgres://user:pass@host:5432/db"},
        ):
            result = get_old_database_url()
            assert result == "postgresql+psycopg://user:pass@host:5432/db"


class TestMigrationConfig:
    """Test MigrationConfig class."""

    def test_init_defaults(self) -> None:
        """Test initialization with defaults."""
        config = MigrationConfig()
        assert config.batch_size == 1000
        assert config.dry_run is False
        assert config.enabled_tables is None
        assert isinstance(config.old_database_url, str)

    def test_init_custom(self) -> None:
        """Test initialization with custom values."""
        config = MigrationConfig(
            old_database_url="postgresql://test",
            batch_size=500,
            dry_run=True,
            enabled_tables={"guild", "guild_config"},
        )
        assert config.old_database_url == "postgresql://test"
        assert config.batch_size == 500
        assert config.dry_run is True
        assert config.enabled_tables == {"guild", "guild_config"}

    def test_is_table_enabled_all_tables(self) -> None:
        """Test is_table_enabled when all tables enabled."""
        config = MigrationConfig(enabled_tables=None)
        assert config.is_table_enabled("guild") is True
        assert config.is_table_enabled("cases") is True
        assert config.is_table_enabled("any_table") is True

    def test_is_table_enabled_specific_tables(self) -> None:
        """Test is_table_enabled with specific table set."""
        config = MigrationConfig(enabled_tables={"guild", "cases"})
        assert config.is_table_enabled("guild") is True
        assert config.is_table_enabled("cases") is True
        assert config.is_table_enabled("guild_config") is False
        assert config.is_table_enabled("other_table") is False

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        config = MigrationConfig(
            old_database_url="postgresql://user:password@host:5432/db",
            batch_size=500,
            dry_run=True,
            enabled_tables={"guild"},
        )
        result = config.to_dict()
        assert result["batch_size"] == 500
        assert result["dry_run"] is True
        assert result["enabled_tables"] == ["guild"]
        # URL should be sanitized
        assert "password" not in result["old_database_url"]
        assert "***" in result["old_database_url"]

    def test_to_dict_sanitizes_url(self) -> None:
        """Test that to_dict sanitizes database URL."""
        config = MigrationConfig(
            old_database_url="postgresql://user:secret@host:5432/db",
        )
        result = config.to_dict()
        assert "secret" not in result["old_database_url"]
        assert "***" in result["old_database_url"]
