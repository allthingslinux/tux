"""
🚀 Database Service Tests - Hybrid Architecture

This test suite demonstrates the hybrid approach:
- UNIT TESTS: Fast sync SQLModel operations using py-pglite
- INTEGRATION TESTS: Full async DatabaseService testing with PostgreSQL

Test Categories:
- @pytest.mark.unit: Fast tests using db_session fixture (py-pglite)
- @pytest.mark.integration: Full async tests using async_db_service fixture (PostgreSQL)

Run modes:
- pytest tests/unit/test_database_service.py                    # Unit tests only
- pytest tests/unit/test_database_service.py --integration     # All tests
- pytest tests/unit/test_database_service.py --unit-only       # Unit tests only
"""

import pytest
from sqlalchemy import text
from sqlmodel import SQLModel, Session, select

from tux.database.models.models import Guild, GuildConfig
from tux.database.service import DatabaseService


# =============================================================================
# UNIT TESTS - Fast Sync SQLModel + py-pglite
# =============================================================================

class TestDatabaseModelsUnit:
    """🏃‍♂️ Unit tests for database models using sync SQLModel + py-pglite."""

    @pytest.mark.unit
    def test_guild_model_creation(self, db_session: Session) -> None:
        """Test Guild model creation and basic operations."""
        # Create guild using sync SQLModel
        guild = Guild(guild_id=123456789, case_count=0)
        db_session.add(guild)
        db_session.commit()
        db_session.refresh(guild)

        # Verify creation
        assert guild.guild_id == 123456789
        assert guild.case_count == 0
        assert guild.guild_joined_at is not None

        # Test query
        result = db_session.get(Guild, 123456789)
        assert result is not None
        assert result.guild_id == 123456789

    @pytest.mark.unit
    def test_guild_config_model_creation(self, db_session: Session) -> None:
        """Test GuildConfig model creation and relationships."""
        # Create guild first
        guild = Guild(guild_id=123456789, case_count=0)
        db_session.add(guild)
        db_session.commit()

        # Create config
        config = GuildConfig(
            guild_id=123456789,
            prefix="!",
            mod_log_id=555666777888999000,
            audit_log_id=555666777888999001,
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        # Verify creation
        assert config.guild_id == 123456789
        assert config.prefix == "!"
        assert config.mod_log_id == 555666777888999000

        # Test relationship
        guild_from_config = db_session.get(Guild, config.guild_id)
        assert guild_from_config is not None
        assert guild_from_config.guild_id == guild.guild_id

    @pytest.mark.unit
    def test_model_serialization(self, db_session: Session) -> None:
        """Test model to_dict serialization."""
        guild = Guild(guild_id=123456789, case_count=5)
        db_session.add(guild)
        db_session.commit()
        db_session.refresh(guild)

        # Test serialization
        guild_dict = guild.to_dict()
        assert isinstance(guild_dict, dict)
        assert guild_dict["guild_id"] == 123456789
        assert guild_dict["case_count"] == 5

    @pytest.mark.unit
    def test_multiple_guilds_query(self, db_session: Session) -> None:
        """Test querying multiple guilds."""
        # Create multiple guilds
        guilds_data = [
            Guild(guild_id=123456789, case_count=1),
            Guild(guild_id=123456790, case_count=2),
            Guild(guild_id=123456791, case_count=3),
        ]

        for guild in guilds_data:
            db_session.add(guild)
        db_session.commit()

        # Query all guilds
        statement = select(Guild)
        results = db_session.exec(statement).unique().all()
        assert len(results) == 3

        # Test ordering
        statement = select(Guild).order_by(Guild.case_count)
        results = db_session.exec(statement).unique().all()
        assert results[0].case_count == 1
        assert results[2].case_count == 3

    @pytest.mark.unit
    def test_database_constraints(self, db_session: Session) -> None:
        """Test database constraints and validation."""
        # Test unique guild_id constraint
        guild1 = Guild(guild_id=123456789, case_count=0)
        guild2 = Guild(guild_id=123456789, case_count=1)  # Same ID

        db_session.add(guild1)
        db_session.commit()

        # This should raise an integrity error
        db_session.add(guild2)
        with pytest.raises(Exception):  # SQLAlchemy integrity error
            db_session.commit()

    @pytest.mark.unit
    def test_raw_sql_execution(self, db_session: Session) -> None:
        """Test raw SQL execution with py-pglite."""
        # Test basic query
        result = db_session.execute(text("SELECT 1 as test_value"))
        value = result.scalar()
        assert value == 1

        # Test PostgreSQL-specific features work with py-pglite
        result = db_session.execute(text("SELECT version()"))
        version = result.scalar()
        assert "PostgreSQL" in version


# =============================================================================
# INTEGRATION TESTS - Full Async DatabaseService + Real PostgreSQL
# =============================================================================

class TestDatabaseServiceIntegration:
    """🌐 Integration tests for DatabaseService using async SQLModel + PostgreSQL."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_service_initialization(self, async_db_service: DatabaseService) -> None:
        """Test async database service initialization."""
        assert async_db_service.is_connected() is True

        # Test health check
        health = await async_db_service.health_check()
        assert health["status"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_session_operations(self, async_db_service: DatabaseService) -> None:
        """Test async session operations with DatabaseService."""
        # Test session creation
        async with async_db_service.session() as session:
            # Create guild through async session
            guild = Guild(guild_id=123456789, case_count=0)
            session.add(guild)
            await session.commit()

            # Query through async session
            result = await session.get(Guild, 123456789)
            assert result is not None
            assert result.guild_id == 123456789

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_controllers_access(self, async_db_service: DatabaseService) -> None:
        """Test async controller access through DatabaseService."""
        # Test guild controller
        guild_controller = async_db_service.guild
        assert guild_controller is not None

        # Test controller operation
        guild = await guild_controller.get_or_create_guild(guild_id=123456789)
        assert guild.guild_id == 123456789

        # Test guild config controller
        config_controller = async_db_service.guild_config
        assert config_controller is not None

        config = await config_controller.get_or_create_config(
            guild_id=123456789,
            prefix="!test",
        )
        assert config.guild_id == 123456789
        assert config.prefix == "!test"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_execute_query_utility(self, async_db_service: DatabaseService) -> None:
        """Test execute_query utility with async operations."""
        async def create_test_guild(session):
            guild = Guild(guild_id=999888777, case_count=42)
            session.add(guild)
            await session.commit()
            await session.refresh(guild)
            return guild

        result = await async_db_service.execute_query(create_test_guild, "create test guild")
        assert result.guild_id == 999888777
        assert result.case_count == 42

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_transaction_utility(self, async_db_service: DatabaseService) -> None:
        """Test execute_transaction utility."""
        async def transaction_operation():
            async with async_db_service.session() as session:
                guild = Guild(guild_id=888777666, case_count=10)
                session.add(guild)
                await session.commit()
                return "transaction_completed"

        result = await async_db_service.execute_transaction(transaction_operation)
        assert result == "transaction_completed"

        # Verify the guild was created
        async with async_db_service.session() as session:
            guild = await session.get(Guild, 888777666)
            assert guild is not None
            assert guild.case_count == 10

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_connection_lifecycle(self, disconnected_async_db_service: DatabaseService) -> None:
        """Test async connection lifecycle management."""
        service = disconnected_async_db_service

        # Initially disconnected
        assert service.is_connected() is False

        # Connect
        await service.connect()
        assert service.is_connected() is True

        # Disconnect
        await service.disconnect()
        assert service.is_connected() is False


# =============================================================================
# PERFORMANCE COMPARISON TESTS
# =============================================================================

class TestPerformanceComparison:
    """⚡ Compare performance between unit tests (py-pglite) and integration tests."""

    @pytest.mark.unit
    def test_unit_test_performance(self, db_session: Session, benchmark) -> None:
        """Benchmark unit test performance with py-pglite."""
        import random

        def create_guild():
            # Use random guild ID to avoid duplicate key conflicts during benchmarking
            guild_id = random.randint(100000000000, 999999999999)
            guild = Guild(guild_id=guild_id, case_count=0)
            db_session.add(guild)
            db_session.commit()
            db_session.refresh(guild)
            return guild

        result = benchmark(create_guild)
        assert result.guild_id is not None
        assert result.case_count == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_test_performance(self, async_db_service: DatabaseService, benchmark) -> None:
        """Benchmark integration test performance with PostgreSQL."""
        async def create_guild_async():
            async with async_db_service.session() as session:
                guild = Guild(guild_id=123456789, case_count=0)
                session.add(guild)
                await session.commit()
                await session.refresh(guild)
                return guild

        # Note: async benchmarking requires special handling
        result = await create_guild_async()
        assert result.guild_id == 123456789


# =============================================================================
# MIXED SCENARIO TESTS
# =============================================================================

class TestMixedScenarios:
    """🔄 Tests that demonstrate the hybrid approach benefits."""

    @pytest.mark.unit
    def test_complex_query_unit(self, db_session: Session) -> None:
        """Complex query test using fast unit testing."""
        # Create test data quickly with py-pglite
        guilds = [
            Guild(guild_id=100000 + i, case_count=i)
            for i in range(10)
        ]

        for guild in guilds:
            db_session.add(guild)
        db_session.commit()

        # Complex query
        statement = select(Guild).where(Guild.case_count > 5).order_by(Guild.case_count.desc())
        results = db_session.exec(statement).unique().all()

        assert len(results) == 4
        assert results[0].case_count == 9

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complex_integration_scenario(self, async_db_service: DatabaseService) -> None:
        """Complex integration scenario using full async stack."""
        # Create guild through controller
        guild = await async_db_service.guild.get_or_create_guild(555666777)

        # Create config through controller
        config = await async_db_service.guild_config.get_or_create_config(
            guild_id=guild.guild_id,
            prefix="!int",
            mod_log_id=888999000111,
        )

        # Verify through async queries
        async with async_db_service.session() as session:
            # Test join operation
            from sqlalchemy.orm import selectinload
            guild_with_config = await session.get(Guild, guild.guild_id)

            assert guild_with_config is not None
            assert guild_with_config.guild_id == config.guild_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
