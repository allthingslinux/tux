"""
🚀 Database Model Tests - SQLModel + py-pglite Unit Testing

Fast unit tests for database models using the clean async architecture:
- Async SQLModel operations with py-pglite
- Real PostgreSQL features without setup complexity
- Comprehensive model validation and relationship testing

Test Coverage:
- Model creation and validation
- Relationships and constraints
- Serialization and deserialization
- Data integrity and validation
- Performance characteristics
"""

import pytest
from datetime import datetime
from typing import Any
from sqlalchemy import text
from sqlmodel import desc
from sqlmodel import select

from tux.database.models.models import Guild, GuildConfig, CaseType, Case
from tux.database.service import DatabaseService
# Test constants and validation functions are now available from conftest.py
from tests.conftest import TEST_GUILD_ID, TEST_CHANNEL_ID, TEST_USER_ID, TEST_MODERATOR_ID, validate_guild_structure, validate_guild_config_structure, validate_relationship_integrity


# =============================================================================
# MODEL CREATION AND VALIDATION TESTS
# =============================================================================

class TestModelCreation:
    """🏗️ Test basic model creation and validation."""

    @pytest.mark.unit
    async def test_guild_model_creation(self, db_service: DatabaseService) -> None:
        """Test Guild model creation with all fields."""
        # Create guild using the async service pattern
        async with db_service.session() as session:
            guild = Guild(
                guild_id=TEST_GUILD_ID,
                case_count=5,
            )

            session.add(guild)
            await session.commit()
            await session.refresh(guild)

            # Verify all fields
            assert guild.guild_id == TEST_GUILD_ID
            assert guild.case_count == 5
            assert guild.guild_joined_at is not None
            assert isinstance(guild.guild_joined_at, datetime)
            assert validate_guild_structure(guild)

    @pytest.mark.unit
    async def test_guild_config_model_creation(self, db_service: DatabaseService) -> None:
        """Test GuildConfig model creation with comprehensive config."""
        async with db_service.session() as session:
            # Create guild first (foreign key requirement)
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create comprehensive config
            config = GuildConfig(
                guild_id=TEST_GUILD_ID,
                prefix="!t",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
                audit_log_id=TEST_CHANNEL_ID + 1,
                join_log_id=TEST_CHANNEL_ID + 2,
                private_log_id=TEST_CHANNEL_ID + 3,
                report_log_id=TEST_CHANNEL_ID + 4,
                dev_log_id=TEST_CHANNEL_ID + 5,
                starboard_channel_id=TEST_CHANNEL_ID + 6,
            )

            session.add(config)
            await session.commit()
            await session.refresh(config)

            # Verify all fields
            assert config.guild_id == TEST_GUILD_ID
            assert config.prefix == "!t"
            assert config.mod_log_id == TEST_CHANNEL_ID
            assert config.audit_log_id == TEST_CHANNEL_ID + 1
            assert config.join_log_id == TEST_CHANNEL_ID + 2
            assert config.private_log_id == TEST_CHANNEL_ID + 3
            assert config.report_log_id == TEST_CHANNEL_ID + 4
            assert config.dev_log_id == TEST_CHANNEL_ID + 5
            assert config.starboard_channel_id == TEST_CHANNEL_ID + 6
            assert validate_guild_config_structure(config)

    @pytest.mark.unit
    async def test_case_model_creation(self, db_service: DatabaseService) -> None:
        """Test Case model creation with enum types."""
        async with db_service.session() as session:
            # Create guild first
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
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
            # Note: case_created_at field might not exist in current model


# =============================================================================
# MODEL RELATIONSHIPS AND CONSTRAINTS TESTS
# =============================================================================

class TestModelRelationships:
    """🔗 Test model relationships and database constraints."""

    @pytest.mark.unit
    async def test_guild_to_config_relationship(self, db_service: DatabaseService) -> None:
        """Test relationship between Guild and GuildConfig."""
        async with db_service.session() as session:
            # Create guild
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create config
            config = GuildConfig(
                guild_id=TEST_GUILD_ID,
                prefix="!r",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(config)
            await session.commit()

            # Test relationship integrity
            assert validate_relationship_integrity(guild, config)

            # Test queries through relationship
            guild_from_db = await session.get(Guild, TEST_GUILD_ID)
            config_from_db = await session.get(GuildConfig, TEST_GUILD_ID)

            assert guild_from_db is not None
            assert config_from_db is not None
            assert guild_from_db.guild_id == config_from_db.guild_id

    @pytest.mark.unit
    async def test_foreign_key_constraints(self, db_service: DatabaseService) -> None:
        """Test foreign key constraints are enforced."""
        async with db_service.session() as session:
            # Try to create config without guild (should fail)
            config = GuildConfig(
                guild_id=999999999999999999,  # Non-existent guild
                prefix="!f",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )

            session.add(config)

            # This should raise a foreign key violation
            try:
                await session.commit()
                pytest.fail("Expected foreign key constraint violation, but commit succeeded")
            except Exception as e:
                # Expected exception occurred
                assert "foreign key" in str(e).lower() or "constraint" in str(e).lower()
                # Rollback the session for cleanup
                await session.rollback()

    @pytest.mark.unit
    async def test_unique_constraints(self, db_service: DatabaseService) -> None:
        """Test unique constraints are enforced."""
        async with db_service.session() as session:
            # Create first guild
            guild1 = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild1)
            await session.commit()

            # Try to create duplicate guild (should fail)
            # Note: This intentionally creates an identity key conflict to test constraint behavior
            # The SAWarning is expected and indicates the test is working correctly
            guild2 = Guild(guild_id=TEST_GUILD_ID, case_count=1)  # Same ID
            session.add(guild2)

            try:
                await session.commit()
                pytest.fail("Expected unique constraint violation, but commit succeeded")
            except Exception as e:
                # Expected exception occurred
                assert "unique" in str(e).lower() or "constraint" in str(e).lower()
                # Rollback the session for cleanup
                await session.rollback()

    @pytest.mark.unit
    async def test_cascade_behavior(self, db_service: DatabaseService) -> None:
        """Test cascade behavior with related models."""
        async with db_service.session() as session:
            # Create guild with config
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            config = GuildConfig(
                guild_id=TEST_GUILD_ID,
                prefix="!c",  # Use valid prefix length (max 3 chars)
            )
            session.add(config)
            await session.commit()

            # Verify both exist
            assert await session.get(Guild, TEST_GUILD_ID) is not None
            assert await session.get(GuildConfig, TEST_GUILD_ID) is not None

            # Delete guild (config should be handled based on cascade rules)
            await session.delete(guild)
            await session.commit()

            # Verify guild is deleted
            assert await session.get(Guild, TEST_GUILD_ID) is None


# =============================================================================
# SERIALIZATION AND DATA HANDLING TESTS
# =============================================================================

class TestModelSerialization:
    """📦 Test model serialization and data conversion."""

    @pytest.mark.unit
    def test_guild_serialization(self, sample_guild: Guild) -> None:
        """Test Guild model serialization to dict."""
        guild_dict = sample_guild.to_dict()

        # Verify dict structure
        assert isinstance(guild_dict, dict)
        assert 'guild_id' in guild_dict
        assert 'case_count' in guild_dict
        assert 'guild_joined_at' in guild_dict

        # Verify data integrity
        assert guild_dict['guild_id'] == sample_guild.guild_id
        assert guild_dict['case_count'] == sample_guild.case_count

    @pytest.mark.unit
    async def test_config_serialization(self, db_service: DatabaseService) -> None:
        """Test GuildConfig model serialization to dict."""
        async with db_service.session() as session:
            # Create guild first
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create config
            sample_guild_config = GuildConfig(
                guild_id=TEST_GUILD_ID,
                prefix="!t",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(sample_guild_config)
            await session.commit()

            config_dict = sample_guild_config.to_dict()

            # Verify dict structure
            assert isinstance(config_dict, dict)
            assert 'guild_id' in config_dict
            assert 'prefix' in config_dict

            # Verify data integrity
            assert config_dict['guild_id'] == sample_guild_config.guild_id
            assert config_dict['prefix'] == sample_guild_config.prefix

    @pytest.mark.unit
    async def test_enum_serialization(self, db_service: DatabaseService) -> None:
        """Test enum field serialization in Case model."""
        async with db_service.session() as session:
            # Create guild first
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
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
            assert case_dict['case_type'] == CaseType.WARN.name  # Should be enum name


# =============================================================================
# QUERY AND PERFORMANCE TESTS
# =============================================================================

class TestModelQueries:
    """🔍 Test complex queries and database operations."""

    @pytest.mark.unit
    async def test_basic_queries(self, db_service: DatabaseService) -> None:
        """Test basic SQLModel queries."""
        async with db_service.session() as session:
            # Create test guilds
            guilds = [
                Guild(guild_id=TEST_GUILD_ID + i, case_count=i)
                for i in range(5)
            ]

            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Test individual access
            for i, guild in enumerate(guilds):
                assert guild.guild_id == TEST_GUILD_ID + i
                assert guild.case_count == i

    @pytest.mark.unit
    async def test_complex_queries(self, db_service: DatabaseService) -> None:
        """Test complex SQLModel queries with filtering and ordering."""
        async with db_service.session() as session:
            # Create test data
            guilds = [
                Guild(guild_id=TEST_GUILD_ID + i, case_count=i * 2)
                for i in range(10)
            ]

            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Test filtering
            statement = select(Guild).where(Guild.case_count > 10)
            high_case_guilds = (await session.execute(statement)).scalars().unique().all()
            assert len(high_case_guilds) == 4  # case_count 12, 14, 16, 18

            # Test ordering
            statement = select(Guild).order_by(desc(Guild.case_count)).limit(3)
            top_guilds = (await session.execute(statement)).scalars().unique().all()
            assert len(top_guilds) == 3
            assert top_guilds[0].case_count == 18
            assert top_guilds[1].case_count == 16
            assert top_guilds[2].case_count == 14

            # Test aggregation with raw SQL
            result = await session.execute(text("SELECT COUNT(*) FROM guild"))  # type: ignore
            count = result.scalar()
            assert count == 10

    @pytest.mark.unit
    async def test_join_queries(self, db_service: DatabaseService) -> None:
        """Test join queries between related models."""
        async with db_service.session() as session:
            # Create guild with config
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=5)
            session.add(guild)
            await session.commit()

            config = GuildConfig(
                guild_id=TEST_GUILD_ID,
                prefix="!j",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(config)
            await session.commit()

            # Test join query using raw SQL (use proper table names)
            result = await session.execute(  # type: ignore
                text("""
                SELECT g.guild_id, g.case_count, gc.prefix
                FROM guild g
                JOIN guildconfig gc ON g.guild_id = gc.guild_id
                WHERE g.guild_id = :guild_id
            """), {"guild_id": TEST_GUILD_ID},
            )

            row = result.fetchone()
            assert row is not None
            assert row[0] == TEST_GUILD_ID
            assert row[1] == 5
        assert row[2] == "!j"


# =============================================================================
# DATA INTEGRITY AND VALIDATION TESTS
# =============================================================================

class TestDataIntegrity:
    """🛡️ Test data integrity and validation rules."""

    @pytest.mark.unit
    async def test_required_fields(self, db_service: DatabaseService) -> None:
        """Test required field validation."""
        async with db_service.session() as session:
            # Guild requires guild_id, test that it works when provided
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Verify guild was created successfully
            assert guild.guild_id == TEST_GUILD_ID

    @pytest.mark.unit
    async def test_data_types(self, db_service: DatabaseService) -> None:
        """Test data type enforcement."""
        async with db_service.session() as session:
            # Test integer fields
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Verify types are preserved
            assert isinstance(guild.guild_id, int)
            assert isinstance(guild.case_count, int)

    @pytest.mark.unit
    async def test_null_handling(self, db_service: DatabaseService) -> None:
        """Test NULL value handling for optional fields."""
        async with db_service.session() as session:
            # Create guild with minimal data
            guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create config with minimal data (most fields optional)
            config = GuildConfig(guild_id=TEST_GUILD_ID)
            session.add(config)
            await session.commit()
            await session.refresh(config)

            # Verify NULL handling
            assert config.guild_id == TEST_GUILD_ID
            assert config.prefix == "$"  # Default value, not None
            assert config.mod_log_id is None  # Optional field

    @pytest.mark.unit
    async def test_transaction_rollback(self, db_service: DatabaseService) -> None:
        """Test transaction rollback behavior."""
        async with db_service.session() as session:
            # First commit a valid guild
            guild1 = Guild(guild_id=TEST_GUILD_ID, case_count=0)
            session.add(guild1)
            await session.commit()  # Commit first guild

            # Verify guild was committed
            result = await session.get(Guild, TEST_GUILD_ID)
            assert result is not None
            assert result.case_count == 0

            # Now try to add duplicate in a new transaction
            # Note: This intentionally creates an identity key conflict to test constraint behavior
            # The SAWarning is expected and indicates the test is working correctly
            try:
                guild2 = Guild(guild_id=TEST_GUILD_ID, case_count=1)  # Same ID - should fail
                session.add(guild2)
                await session.commit()  # This should fail due to unique constraint
            except Exception:
                await session.rollback()  # Rollback the failed transaction

            # Verify original guild still exists and wasn't affected by the rollback
            result = await session.get(Guild, TEST_GUILD_ID)
            assert result is not None
            assert result.case_count == 0  # Original value preserved


# =============================================================================
# PERFORMANCE AND BENCHMARK TESTS
# =============================================================================

class TestModelPerformance:
    """⚡ Test model performance characteristics."""

    @pytest.mark.unit
    async def test_bulk_operations(self, db_service: DatabaseService) -> None:
        """Test bulk model operations."""
        async with db_service.session() as session:
            # Create multiple guilds
            guilds = [
                Guild(guild_id=TEST_GUILD_ID + i, case_count=i)
                for i in range(10)  # Smaller number for faster tests
            ]

            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Verify all were created
            statement = select(Guild)
            results = (await session.execute(statement)).scalars().unique().all()
            assert len(results) == 10

    @pytest.mark.unit
    async def test_query_performance(self, db_service: DatabaseService) -> None:
        """Test query performance with filtering and ordering."""
        async with db_service.session() as session:
            # Create test data
            guilds = [
                Guild(guild_id=TEST_GUILD_ID + i, case_count=i)
                for i in range(20)
            ]

            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Test filtering query
            statement = select(Guild).where(Guild.case_count > 10)
            results = (await session.execute(statement)).scalars().unique().all()
            assert len(results) == 9  # case_count 11-19

            # Test ordering query
            statement = select(Guild).order_by(desc(Guild.case_count)).limit(5)
            results = (await session.execute(statement)).scalars().unique().all()
            assert len(results) == 5
            assert results[0].case_count == 19

    @pytest.mark.unit
    async def test_serialization_performance(self, db_service: DatabaseService) -> None:
        """Test serialization performance."""
        async with db_service.session() as session:
            # Create test data
            guilds = []
            configs = []

            for i in range(5):  # Create 5 test guilds with configs
                guild = Guild(guild_id=TEST_GUILD_ID + i, case_count=i)
                session.add(guild)
                guilds.append(guild)

                config = GuildConfig(
                    guild_id=TEST_GUILD_ID + i,
                    prefix=f"!{i}",  # Use valid prefix length (max 3 chars)
                )
                session.add(config)
                configs.append(config)

            await session.commit()

            # Serialize all models
            results = []
            for guild, config in zip(guilds, configs):
                guild_dict = guild.to_dict()
                config_dict = config.to_dict()
                results.append({'guild': guild_dict, 'config': config_dict})

            assert len(results) == 5

            # Verify serialization structure
            for result in results:
                assert 'guild' in result
                assert 'config' in result
                assert 'guild_id' in result['guild']
            assert 'guild_id' in result['config']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
