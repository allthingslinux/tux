"""
🚀 Database Model Creation Tests - SQLModel + py-pglite Unit Testing.

Tests for basic model creation and validation.
"""

from datetime import datetime

import pytest

from tests.fixtures import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    validate_guild_config_structure,
    validate_guild_structure,
)
from tux.database.models.models import Case, CaseType, Guild, GuildConfig
from tux.database.service import DatabaseService


class TestModelCreation:
    """🏗️ Test basic model creation and validation."""

    @pytest.mark.unit
    async def test_guild_model_creation(self, db_service: DatabaseService) -> None:
        """Test Guild model creation with all fields."""
        # Create guild using the async service pattern
        async with db_service.session() as session:
            guild = Guild(
                id=TEST_GUILD_ID,
                case_count=5,
            )

            session.add(guild)
            await session.commit()
            await session.refresh(guild)

            # Verify all fields
            assert guild.id == TEST_GUILD_ID
            assert guild.case_count == 5
            assert guild.guild_joined_at is not None
            assert isinstance(guild.guild_joined_at, datetime)
            assert validate_guild_structure(guild)

    @pytest.mark.unit
    async def test_guild_config_model_creation(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Test GuildConfig model creation with comprehensive config."""
        async with db_service.session() as session:
            # Create guild first (foreign key requirement)
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create comprehensive config
            config = GuildConfig(
                id=TEST_GUILD_ID,
                prefix="!t",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
                audit_log_id=TEST_CHANNEL_ID + 1,
                join_log_id=TEST_CHANNEL_ID + 2,
                private_log_id=TEST_CHANNEL_ID + 3,
                report_log_id=TEST_CHANNEL_ID + 4,
                dev_log_id=TEST_CHANNEL_ID + 5,
            )

            session.add(config)
            await session.commit()
            await session.refresh(config)

            # Verify all fields
            assert config.id == TEST_GUILD_ID
            assert config.prefix == "!t"
            assert config.mod_log_id == TEST_CHANNEL_ID
            assert config.audit_log_id == TEST_CHANNEL_ID + 1
            assert config.join_log_id == TEST_CHANNEL_ID + 2
            assert config.private_log_id == TEST_CHANNEL_ID + 3
            assert config.report_log_id == TEST_CHANNEL_ID + 4
            assert config.dev_log_id == TEST_CHANNEL_ID + 5
            assert validate_guild_config_structure(config)

    @pytest.mark.unit
    async def test_case_model_creation(self, db_service: DatabaseService) -> None:
        """Test Case model creation with enum types."""
        async with db_service.session() as session:
            # Create guild first
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create case with enum
            case = Case(
                guild_id=TEST_GUILD_ID,
                case_type=CaseType.BAN,
                case_number=1,
                case_reason="Test ban reason",
                case_user_id=12345,
                case_moderator_id=67890,
            )

            session.add(case)
            await session.commit()
            await session.refresh(case)

            # Verify case creation and enum handling
            assert case.guild_id == TEST_GUILD_ID
            assert case.case_type == CaseType.BAN
            assert case.case_number == 1
            assert case.case_reason == "Test ban reason"
            assert case.case_user_id == 12345
            assert case.case_moderator_id == 67890
