"""Tests for migration validator."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tux.database.models import Guild, GuildConfig
from tux.database.service import DatabaseService
from tux.plugins.v0_1_db_migrate.mapper import (
    ModelMapper,
)
from tux.plugins.v0_1_db_migrate.validator import (
    MigrationValidator,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestMigrationValidator:
    """Test MigrationValidator class."""

    @pytest.fixture
    def mapper(self) -> ModelMapper:
        """Create test mapper."""
        return ModelMapper()

    @pytest.fixture
    def old_db_engine(self):
        """Create old database engine."""
        return create_engine("sqlite:///:memory:")

    @pytest.fixture
    async def db_service(self, pglite_engine) -> DatabaseService:
        """Create test database service."""
        service = DatabaseService(echo=False)
        service._engine = pglite_engine

        service._session_factory = async_sessionmaker(
            pglite_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        return service

    @pytest.fixture
    def validator(
        self,
        mapper: ModelMapper,
        old_db_engine,
        db_service: DatabaseService,
    ) -> MigrationValidator:
        """Create test validator."""
        return MigrationValidator(mapper, old_db_engine, db_service)

    def test_get_old_row_count(
        self,
        validator: MigrationValidator,
        old_db_engine,
    ) -> None:
        """Test getting row count from old database."""
        # Setup old database
        with old_db_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY)"),
            )
            conn.execute(text("INSERT INTO Guild (guild_id) VALUES (1), (2), (3)"))
            conn.commit()

        count = validator.get_old_row_count("Guild")
        assert count == 3

    def test_get_old_row_count_no_engine(self) -> None:
        """Test getting row count without engine."""
        mapper = ModelMapper()
        service = DatabaseService()
        validator = MigrationValidator(mapper, None, service)

        count = validator.get_old_row_count("Guild")
        assert count == 0  # Should return 0 when engine is None

    async def test_get_new_row_count(self, validator: MigrationValidator) -> None:
        """Test getting row count from new database."""
        # Create some guilds
        async with validator.db_service.session() as session:
            guild1 = Guild(id=111111111, case_count=0)
            guild2 = Guild(id=222222222, case_count=0)
            session.add(guild1)
            session.add(guild2)
            await session.commit()

        count = await validator.get_new_row_count("guild")
        assert count == 2

    async def test_validate_row_counts_match(
        self,
        validator: MigrationValidator,
        old_db_engine,
    ) -> None:
        """Test row count validation when counts match."""
        # Setup old database
        with old_db_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY)"),
            )
            conn.execute(text("INSERT INTO Guild (guild_id) VALUES (123456789)"))
            conn.commit()

        # Create matching guild in new database
        async with validator.db_service.session() as session:
            guild = Guild(id=123456789, case_count=0)
            session.add(guild)
            await session.commit()

        validator.old_engine = old_db_engine
        results = await validator.validate_row_counts()

        assert "guild" in results
        assert results["guild"]["match"] is True
        assert results["guild"]["old_count"] == 1
        assert results["guild"]["new_count"] == 1

    async def test_validate_row_counts_mismatch(
        self,
        validator: MigrationValidator,
        old_db_engine,
    ) -> None:
        """Test row count validation when counts don't match."""
        # Setup old database with 2 rows
        with old_db_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY)"),
            )
            conn.execute(
                text("INSERT INTO Guild (guild_id) VALUES (111111111), (222222222)"),
            )
            conn.commit()

        # Create only 1 row in new database
        async with validator.db_service.session() as session:
            guild = Guild(id=111111111, case_count=0)
            session.add(guild)
            await session.commit()

        validator.old_engine = old_db_engine
        results = await validator.validate_row_counts()

        assert "guild" in results
        assert results["guild"]["match"] is False
        assert results["guild"]["old_count"] == 2
        assert results["guild"]["new_count"] == 1
        assert results["guild"]["difference"] == -1

    async def test_validate_relationships(
        self,
        validator: MigrationValidator,
    ) -> None:
        """Test relationship validation."""
        # Create guild and config
        async with validator.db_service.session() as session:
            guild = Guild(id=123456789, case_count=0)
            config = GuildConfig(id=123456789, prefix="$")
            session.add(guild)
            session.add(config)
            await session.commit()

        result = await validator.validate_relationships()

        assert "relationships_checked" in result
        assert "relationships_valid" in result
        assert result["relationships_valid"] >= 1

    async def test_validate_sample_data(
        self,
        validator: MigrationValidator,
    ) -> None:
        """Test sample data validation."""
        # Create sample guild
        async with validator.db_service.session() as session:
            guild = Guild(id=123456789, case_count=5)
            session.add(guild)
            await session.commit()

        result = await validator.validate_sample_data("guild")

        assert "samples_checked" in result
        assert "samples_valid" in result

    async def test_generate_validation_report(
        self,
        validator: MigrationValidator,
        old_db_engine,
    ) -> None:
        """Test generating full validation report."""
        # Setup old database
        with old_db_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY)"),
            )
            conn.execute(text("INSERT INTO Guild (guild_id) VALUES (123456789)"))
            conn.commit()

        # Create matching guild in new database
        async with validator.db_service.session() as session:
            guild = Guild(id=123456789, case_count=0)
            session.add(guild)
            await session.commit()

        validator.old_engine = old_db_engine
        report = await validator.generate_validation_report()

        assert "row_counts" in report
        assert "relationships" in report
        assert "constraints" in report
        assert "samples" in report
        assert "summary" in report
        assert report["summary"]["total_tables"] > 0
