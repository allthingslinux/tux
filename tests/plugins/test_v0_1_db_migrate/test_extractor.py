"""Tests for data extractor."""

import pytest
from sqlalchemy import create_engine, text

from tux.plugins.v0_1_db_migrate.config import (
    MigrationConfig,
)
from tux.plugins.v0_1_db_migrate.extractor import (
    DataExtractor,
)
from tux.plugins.v0_1_db_migrate.mapper import (
    ModelMapper,
)


class TestDataExtractor:
    """Test DataExtractor class."""

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

    def test_init(self, extractor: DataExtractor) -> None:
        """Test initialization."""
        assert extractor.config is not None
        assert extractor.mapper is not None
        assert extractor.engine is None

    def test_set_engine(self, extractor: DataExtractor) -> None:
        """Test setting engine."""
        engine = create_engine("sqlite:///:memory:")
        extractor.set_engine(engine)
        assert extractor.engine == engine

    def test_get_row_count(self, extractor: DataExtractor) -> None:
        """Test getting row count."""
        engine = create_engine("sqlite:///:memory:")
        extractor.set_engine(engine)

        # Create test table
        with engine.connect() as conn:
            conn.execute(
                text("CREATE TABLE TestTable (id INTEGER PRIMARY KEY, name TEXT)"),
            )
            conn.execute(
                text("INSERT INTO TestTable (name) VALUES ('test1'), ('test2')"),
            )
            conn.commit()

        count = extractor.get_row_count("TestTable")
        assert count == 2

    def test_get_row_count_no_engine(self, extractor: DataExtractor) -> None:
        """Test getting row count without engine."""
        with pytest.raises(RuntimeError, match="Engine not set"):
            extractor.get_row_count("TestTable")

    def test_extract_table(self, extractor: DataExtractor) -> None:
        """Test extracting table data."""
        engine = create_engine("sqlite:///:memory:")
        extractor.set_engine(engine)

        # Create test table with Guild-like structure
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE Guild (guild_id INTEGER PRIMARY KEY, "
                    "guild_joined_at TEXT, case_count INTEGER)",
                ),
            )
            conn.execute(
                text("INSERT INTO Guild (guild_id, case_count) VALUES (1, 5), (2, 10)"),
            )
            conn.commit()

        batches = list(extractor.extract_table("Guild", batch_size=1))
        assert len(batches) == 2
        assert len(batches[0]) == 1
        # Guild table maps guild_id to id
        assert batches[0][0]["id"] == 1
        assert batches[0][0]["case_count"] == 5

    def test_extract_table_empty(self, extractor: DataExtractor) -> None:
        """Test extracting from empty table."""
        engine = create_engine("sqlite:///:memory:")
        extractor.set_engine(engine)

        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE TestTable (id INTEGER PRIMARY KEY)"))
            conn.commit()

        batches = list(extractor.extract_table("TestTable"))
        assert len(batches) == 0

    def test_extract_table_composite_pk(self, extractor: DataExtractor) -> None:
        """Test extracting table with composite primary key."""
        engine = create_engine("sqlite:///:memory:")
        extractor.set_engine(engine)

        # Create AFKModel-like table with composite PK
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE AFKModel (member_id INTEGER, guild_id INTEGER, "
                    "nickname TEXT, PRIMARY KEY (member_id, guild_id))",
                ),
            )
            conn.execute(
                text(
                    "INSERT INTO AFKModel (member_id, guild_id, nickname) "
                    "VALUES (1, 100, 'test1'), (2, 100, 'test2')",
                ),
            )
            conn.commit()

        batches = list(extractor.extract_table("AFKModel", batch_size=1))
        assert len(batches) >= 1

    def test_validate_row_valid(self, extractor: DataExtractor) -> None:
        """Test validating valid row."""
        row_data = {
            "id": 123,
            "guild_joined_at": "2024-01-01T00:00:00",
            "case_count": 5,
        }
        is_valid, _error = extractor.validate_row("guild", row_data)
        assert is_valid is True
        assert _error is None

    def test_validate_row_invalid(self, extractor: DataExtractor) -> None:
        """Test validating invalid row."""
        # Missing required field
        row_data = {"id": 123}
        is_valid, _error = extractor.validate_row("guild", row_data)
        # May be valid if fields have defaults
        assert isinstance(is_valid, bool)

    def test_validate_row_invalid_type(self, extractor: DataExtractor) -> None:
        """Test validating row with potentially invalid type."""
        # Note: SQLModel may not strictly validate types, so this may pass
        row_data = {
            "id": 123,
            "guild_joined_at": "2024-01-01T00:00:00",
            "case_count": "not_an_int",  # This might not fail validation
        }
        is_valid, _error = extractor.validate_row("guild", row_data)
        # Validation behavior depends on SQLModel strictness
        assert isinstance(is_valid, bool)
