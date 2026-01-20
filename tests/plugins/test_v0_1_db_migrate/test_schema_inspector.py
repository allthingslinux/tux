"""Tests for schema inspector."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from tux.plugins.v0_1_db_migrate.config import (
    MigrationConfig,
)
from tux.plugins.v0_1_db_migrate.schema_inspector import (
    SchemaInspector,
)


class TestSchemaInspector:
    """Test SchemaInspector class."""

    def test_init(self) -> None:
        """Test initialization."""
        config = MigrationConfig()
        inspector = SchemaInspector(config)
        assert inspector.config == config
        assert inspector.engine is None

    def test_connect_success(self) -> None:
        """Test successful connection."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)

        inspector.connect()

        assert inspector.engine is not None
        inspector.disconnect()

    def test_connect_failure(self) -> None:
        """Test connection failure."""
        config = MigrationConfig(
            old_database_url="postgresql://invalid:invalid@invalid:9999/invalid",
        )
        inspector = SchemaInspector(config)

        # Should fail due to missing psycopg2 driver or invalid connection
        with pytest.raises((SQLAlchemyError, ImportError, ModuleNotFoundError)):
            inspector.connect()

    def test_disconnect(self) -> None:
        """Test disconnection."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)
        inspector.connect()

        inspector.disconnect()

        assert inspector.engine is None

    def test_disconnect_no_engine(self) -> None:
        """Test disconnection when engine is None."""
        config = MigrationConfig()
        inspector = SchemaInspector(config)

        # Should not raise
        inspector.disconnect()

    def test_get_tables(self) -> None:
        """Test getting table list."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)
        inspector.connect()

        tables = inspector.inspect_tables()

        assert isinstance(tables, list)
        inspector.disconnect()

    def test_get_table_columns(self) -> None:
        """Test getting table columns."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)
        inspector.connect()

        # Create a test table
        with inspector.engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(text("CREATE TABLE test_table (id INTEGER, name TEXT)"))
            conn.commit()

        columns = inspector.inspect_columns("test_table")

        assert isinstance(columns, list)
        column_names = [col["name"] for col in columns]
        assert "id" in column_names
        assert "name" in column_names
        inspector.disconnect()

    def test_get_table_indexes(self) -> None:
        """Test getting table indexes."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)
        inspector.connect()

        # Create a test table with index
        with inspector.engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY)"))
            conn.execute(text("CREATE INDEX idx_test ON test_table(id)"))
            conn.commit()

        indexes = inspector.inspect_indexes("test_table")

        assert isinstance(indexes, list)
        inspector.disconnect()

    def test_get_table_foreign_keys(self) -> None:
        """Test getting table foreign keys."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)
        inspector.connect()

        # Create test tables with FK
        with inspector.engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY)"))
            conn.execute(
                text(
                    "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))",
                ),
            )
            conn.commit()

        relationships = inspector.inspect_relationships()
        fks = [rel for rel in relationships if rel["table"] == "child"]

        assert isinstance(fks, list)
        inspector.disconnect()

    def test_inspect_schema(self) -> None:
        """Test full schema inspection."""
        config = MigrationConfig(old_database_url="sqlite:///:memory:")
        inspector = SchemaInspector(config)
        inspector.connect()

        # Create test tables
        with inspector.engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(
                text("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)"),
            )
            conn.commit()

        schema = inspector.get_schema_report()

        assert isinstance(schema, dict)
        assert "tables" in schema
        assert "test_table" in schema["tables"]
        inspector.disconnect()
