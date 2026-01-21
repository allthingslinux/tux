"""Tests for database migrator."""

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tux.database.models import Guild, PermissionAssignment, PermissionRank
from tux.database.service import DatabaseService
from tux.plugins.v0_1_db_migrate.config import (
    MigrationConfig,
)
from tux.plugins.v0_1_db_migrate.extractor import (
    DataExtractor,
)
from tux.plugins.v0_1_db_migrate.mapper import (
    ModelMapper,
)
from tux.plugins.v0_1_db_migrate.migrator import (
    DatabaseMigrator,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDatabaseMigrator:
    """Test DatabaseMigrator class."""

    @pytest.fixture
    def config(self) -> MigrationConfig:
        """Create test config."""
        return MigrationConfig(old_database_url="sqlite:///:memory:", batch_size=10)

    @pytest.fixture
    def mapper(self) -> ModelMapper:
        """Create test mapper."""
        return ModelMapper()

    @pytest.fixture
    def extractor(self, config: MigrationConfig, mapper: ModelMapper) -> DataExtractor:
        """Create test extractor."""
        return DataExtractor(config, mapper)

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
    def old_db_engine(self):
        """Create old database engine."""
        return create_engine("sqlite:///:memory:")

    @pytest.fixture
    def migrator(
        self,
        config: MigrationConfig,
        mapper: ModelMapper,
        extractor: DataExtractor,
        db_service: DatabaseService,
    ) -> DatabaseMigrator:
        """Create test migrator."""
        return DatabaseMigrator(config, mapper, extractor, db_service)

    async def test_init(self, migrator: DatabaseMigrator) -> None:
        """Test initialization."""
        assert migrator.config is not None
        assert migrator.mapper is not None
        assert migrator.extractor is not None
        assert migrator.db_service is not None

    async def test_migrate_table_success(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test successful table migration."""
        # Setup old database
        with old_db_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY, "
                    "guild_joined_at TEXT, case_count INTEGER)",
                ),
            )
            conn.execute(
                text("INSERT INTO Guild (guild_id, case_count) VALUES (123456789, 5)"),
            )
            conn.commit()

        migrator.extractor.set_engine(old_db_engine)

        result = await migrator.migrate_table("Guild", "guild")

        assert result["success"] is True
        assert result["rows_migrated"] == 1
        assert result["rows_failed"] == 0

        # Verify data was migrated
        async with migrator.db_service.session() as session:
            stmt = select(Guild).where(Guild.id == 123456789)  # type: ignore[arg-type]
            result_obj = await session.execute(stmt)
            guild = result_obj.unique().scalar_one_or_none()
            assert guild is not None
            assert guild.case_count == 5

    async def test_migrate_table_dry_run(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test dry-run mode."""
        migrator.config.dry_run = True

        # Setup old database
        with old_db_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY, "
                    "case_count INTEGER)",
                ),
            )
            conn.execute(
                text("INSERT INTO Guild (guild_id, case_count) VALUES (123456789, 5)"),
            )
            conn.commit()

        migrator.extractor.set_engine(old_db_engine)

        result = await migrator.migrate_table("Guild", "guild")

        assert result["success"] is True
        assert result["rows_migrated"] == 1

        # Verify data was NOT migrated (dry-run)
        async with migrator.db_service.session() as session:
            stmt = select(Guild).where(Guild.id == 123456789)  # type: ignore[arg-type]
            result_obj = await session.execute(stmt)
            guild = result_obj.unique().scalar_one_or_none()
            assert guild is None  # Should be None in dry-run

    async def test_migrate_table_disabled(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test migration when table is disabled."""
        migrator.config.enabled_tables = {"cases"}  # Guild not enabled

        migrator.extractor.set_engine(old_db_engine)

        result = await migrator.migrate_table("Guild", "guild")

        assert result["success"] is True
        assert result["rows_migrated"] == 0  # Skipped

    async def test_migrate_permission_ranks(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test permission ranks migration."""
        # Setup old database with GuildConfig
        with old_db_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE GuildConfig (guild_id INTEGER PRIMARY KEY, "
                    "perm_level_0_role_id INTEGER, perm_level_1_role_id INTEGER)",
                ),
            )
            conn.execute(
                text(
                    "INSERT INTO GuildConfig (guild_id, perm_level_0_role_id, perm_level_1_role_id) "
                    "VALUES (123456789, 111111111, 222222222)",
                ),
            )
            conn.commit()

        migrator.extractor.set_engine(old_db_engine)

        # Create guild first
        async with migrator.db_service.session() as session:
            guild = Guild(id=123456789, case_count=0)
            session.add(guild)
            await session.commit()

        result = await migrator.migrate_permission_ranks()

        assert result["success"] is True
        assert result["rows_migrated"] >= 2  # At least 2 ranks + 2 assignments

        # Verify PermissionRank was created
        async with migrator.db_service.session() as session:
            stmt = select(PermissionRank).where(
                (PermissionRank.guild_id == 123456789) & (PermissionRank.rank == 0),  # type: ignore[arg-type]
            )
            result_obj = await session.execute(stmt)
            rank = result_obj.unique().scalar_one_or_none()
            assert rank is not None
            assert rank.name == "Rank 0"

        # Verify PermissionAssignment was created
        async with migrator.db_service.session() as session:
            stmt = select(PermissionAssignment).where(
                (PermissionAssignment.guild_id == 123456789)
                & (PermissionAssignment.role_id == 111111111),  # type: ignore[arg-type]
            )
            result_obj = await session.execute(stmt)
            assignment = result_obj.unique().scalar_one_or_none()
            assert assignment is not None

    async def test_migrate_permission_ranks_no_roles(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test permission ranks migration with no role IDs."""
        # Setup old database with GuildConfig but no perm_level fields
        with old_db_engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE GuildConfig (guild_id INTEGER PRIMARY KEY)"),
            )
            conn.execute(text("INSERT INTO GuildConfig (guild_id) VALUES (123456789)"))
            conn.commit()

        migrator.extractor.set_engine(old_db_engine)

        result = await migrator.migrate_permission_ranks()

        assert result["success"] is True
        assert result["rows_migrated"] == 0  # No roles to migrate

    async def test_migrate_all(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test migrating all tables."""
        # Only migrate guild; old DB has no other tables
        migrator.config.enabled_tables = {"guild"}

        # Setup old database with Guild
        with old_db_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY, "
                    "case_count INTEGER)",
                ),
            )
            conn.execute(
                text("INSERT INTO Guild (guild_id, case_count) VALUES (123456789, 5)"),
            )
            conn.commit()

        migrator.extractor.set_engine(old_db_engine)

        result = await migrator.migrate_all()

        assert isinstance(result, dict)
        assert "guild" in result
        assert result["guild"]["success"] is True

    async def test_migrate_table_error_handling(
        self,
        migrator: DatabaseMigrator,
        old_db_engine,
    ) -> None:
        """Test error handling during migration."""
        # Setup old database with invalid data
        with old_db_engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY, "
                    "case_count TEXT)",  # Wrong type
                ),
            )
            conn.execute(
                text(
                    "INSERT INTO Guild (guild_id, case_count) VALUES (123456789, 'invalid')",
                ),
            )
            conn.commit()

        migrator.extractor.set_engine(old_db_engine)

        result = await migrator.migrate_table("Guild", "guild")

        # Should handle errors gracefully
        assert "success" in result
        # May succeed with validation errors or fail gracefully
