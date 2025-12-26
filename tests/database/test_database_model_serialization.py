"""
🚀 Database Model Serialization Tests - SQLModel + py-pglite Unit Testing.

Tests for model serialization and data conversion.
"""

import pytest

from tests.fixtures import TEST_CHANNEL_ID, TEST_GUILD_ID
from tux.database.models.models import Case, CaseType, Guild, GuildConfig
from tux.database.service import DatabaseService


class TestModelSerialization:
    """📦 Test model serialization and data conversion."""

    @pytest.mark.unit
    def test_guild_serialization(self, sample_guild: Guild) -> None:
        """Test Guild model serialization to dict."""
        guild_dict = sample_guild.to_dict()

        # Verify dict structure
        assert isinstance(guild_dict, dict)
        assert "id" in guild_dict
        assert "case_count" in guild_dict
        assert "guild_joined_at" in guild_dict

        # Verify data integrity
        assert guild_dict["id"] == sample_guild.id
        assert guild_dict["case_count"] == sample_guild.case_count

    @pytest.mark.unit
    async def test_config_serialization(self, db_service: DatabaseService) -> None:
        """Test GuildConfig model serialization to dict."""
        async with db_service.session() as session:
            # Create guild first
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create config
            sample_guild_config = GuildConfig(
                id=TEST_GUILD_ID,
                prefix="!t",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(sample_guild_config)
            await session.commit()

            config_dict = sample_guild_config.to_dict()

            # Verify dict structure
            assert isinstance(config_dict, dict)
            assert "id" in config_dict
            assert "prefix" in config_dict

            # Verify data integrity
            assert config_dict["id"] == sample_guild_config.id
            assert config_dict["prefix"] == sample_guild_config.prefix

    @pytest.mark.unit
    async def test_enum_serialization(self, db_service: DatabaseService) -> None:
        """Test enum field serialization in Case model."""
        async with db_service.session() as session:
            # Create guild first
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create case with enum
            case = Case(
                guild_id=TEST_GUILD_ID,
                case_type=CaseType.WARN,
                case_number=1,
                case_reason="Test warning",
                case_user_id=12345,
                case_moderator_id=67890,
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)

            # Test enum serialization
            case_dict = case.to_dict()
            assert case_dict["case_type"] == CaseType.WARN.name  # Should be enum name
