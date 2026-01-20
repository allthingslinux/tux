"""
Schema inspector for old Prisma database.

Inspects the schema of the old Prisma/Supabase database to understand
table structure, columns, relationships, and constraints.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .config import MigrationConfig
from .utils import sanitize_database_url


class SchemaInspector:
    """
    Inspect schema of old Prisma database.

    Provides methods to discover tables, columns, relationships,
    and other schema metadata from the old database.

    Attributes
    ----------
    config : MigrationConfig
        Migration configuration.
    engine : Engine | None
        SQLAlchemy sync engine for old database connection.
    """

    def __init__(self, config: MigrationConfig) -> None:
        """
        Initialize schema inspector.

        Parameters
        ----------
        config : MigrationConfig
            Migration configuration with old database URL.
        """
        self.config = config
        self.engine: Engine | None = None

    def connect(self) -> None:
        """
        Connect to the old database.

        Raises
        ------
        SQLAlchemyError
            If connection fails.
        """
        try:
            logger.info(
                f"Connecting to old database: {sanitize_database_url(self.config.old_database_url)}",
            )
            self.engine = create_engine(
                self.config.old_database_url,
                pool_pre_ping=True,
                echo=False,
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.success("Connected to old database")
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to old database: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from the old database."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Disconnected from old database")

    def inspect_tables(self) -> list[str]:
        """
        Inspect all tables in the old database.

        Returns
        -------
        list[str]
            List of table names in the old database.

        Raises
        ------
        RuntimeError
            If not connected to database.
        """
        if not self.engine:
            msg = "Not connected to database. Call connect() first."
            raise RuntimeError(msg)

        try:
            inspector = inspect(self.engine)
            # Use appropriate schema based on database type
            schema = "public" if self.engine.dialect.name == "postgresql" else None
            tables = inspector.get_table_names(schema=schema)
        except SQLAlchemyError as e:
            logger.error(f"Failed to inspect tables: {e}")
            raise
        else:
            logger.info(f"Found {len(tables)} tables in old database")
            return tables

    def inspect_columns(self, table_name: str) -> list[dict[str, Any]]:
        """
        Inspect columns for a specific table.

        Parameters
        ----------
        table_name : str
            Name of the table to inspect.

        Returns
        -------
        list[dict[str, Any]]
            List of column metadata dictionaries with keys:
            - name: Column name
            - type: Column type (string representation)
            - nullable: Whether column is nullable
            - default: Default value (if any)
            - primary_key: Whether column is primary key
            - foreign_keys: List of foreign key relationships

        Raises
        ------
        RuntimeError
            If not connected to database.
        """
        if not self.engine:
            msg = "Not connected to database. Call connect() first."
            raise RuntimeError(msg)

        try:
            inspector = inspect(self.engine)
            # Use appropriate schema based on database type
            schema = "public" if self.engine.dialect.name == "postgresql" else None
            columns = inspector.get_columns(table_name, schema=schema)

            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            pk_columns = set(pk_constraint.get("constrained_columns", []))

            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name, schema=schema)
            fk_map: dict[str, list[dict[str, Any]]] = {}
            for fk in fks:
                for col in fk.get("constrained_columns", []):
                    if col not in fk_map:
                        fk_map[col] = []
                    fk_map[col].append(
                        {
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns", []),
                        },
                    )

            # Build column metadata
            column_metadata: list[dict[str, Any]] = []
            for col in columns:
                col_name = col["name"]
                column_metadata.append(
                    {
                        "name": col_name,
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": col.get("default"),
                        "primary_key": col_name in pk_columns,
                        "foreign_keys": fk_map.get(col_name, []),
                    },
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to inspect columns for table '{table_name}': {e}")
            raise
        else:
            logger.debug(
                f"Inspected {len(column_metadata)} columns in table '{table_name}'",
            )
            return column_metadata

    def inspect_primary_key_constraint(self, table_name: str) -> dict[str, Any]:
        """
        Inspect primary key constraint details for a table.

        Parameters
        ----------
        table_name : str
            Table name to inspect.

        Returns
        -------
        dict[str, Any]
            Primary key constraint details with keys:
            - constraint_name: str
            - columns: list[str]
            - is_composite: bool
        """
        if not self.engine:
            msg = "Not connected to database"
            raise RuntimeError(msg)

        try:
            inspector = inspect(self.engine)
            schema = "public" if self.engine.dialect.name == "postgresql" else None
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)

            constrained_columns = pk_constraint.get("constrained_columns", [])
            constraint_name = pk_constraint.get("name", "unknown")

            return {
                "constraint_name": constraint_name,
                "columns": constrained_columns,
                "is_composite": len(constrained_columns) > 1,
                "column_count": len(constrained_columns),
            }
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to inspect PK constraint for table '{table_name}': {e}",
            )
            raise

    def inspect_relationships(self) -> list[dict[str, Any]]:
        """
        Inspect foreign key relationships in the old database.

        Returns
        -------
        list[dict[str, Any]]
            List of relationship metadata dictionaries with keys:
            - table: Source table name
            - columns: List of column names in source table
            - referred_table: Target table name
            - referred_columns: List of column names in target table

        Raises
        ------
        RuntimeError
            If not connected to database.
        """
        if not self.engine:
            msg = "Not connected to database. Call connect() first."
            raise RuntimeError(msg)

        try:
            inspector = inspect(self.engine)
            tables = self.inspect_tables()
            relationships: list[dict[str, Any]] = []

            # Use appropriate schema based on database type
            schema = "public" if self.engine.dialect.name == "postgresql" else None

            for table_name in tables:
                fks = inspector.get_foreign_keys(table_name, schema=schema)
                relationships.extend(
                    [
                        {
                            "table": table_name,
                            "columns": fk.get("constrained_columns", []),
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns", []),
                        }
                        for fk in fks
                    ],
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to inspect relationships: {e}")
            raise
        else:
            logger.info(f"Found {len(relationships)} foreign key relationships")
            return relationships

    def inspect_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """
        Inspect indexes for a specific table.

        Parameters
        ----------
        table_name : str
            Name of the table to inspect.

        Returns
        -------
        list[dict[str, Any]]
            List of index metadata dictionaries with keys:
            - name: Index name
            - columns: List of column names in index
            - unique: Whether index is unique

        Raises
        ------
        RuntimeError
            If not connected to database.
        """
        if not self.engine:
            msg = "Not connected to database. Call connect() first."
            raise RuntimeError(msg)

        try:
            inspector = inspect(self.engine)
            # Use appropriate schema based on database type
            schema = "public" if self.engine.dialect.name == "postgresql" else None
            indexes = inspector.get_indexes(table_name, schema=schema)

            index_metadata = [
                {
                    "name": idx["name"],
                    "columns": idx.get("column_names", []),
                    "unique": idx.get("unique", False),
                }
                for idx in indexes
            ]

            logger.debug(
                f"Inspected {len(index_metadata)} indexes in table '{table_name}'",
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to inspect indexes for table '{table_name}': {e}")
            raise
        else:
            return index_metadata

    def get_schema_report(self) -> dict[str, Any]:
        """
        Generate comprehensive schema report for the old database.

        Returns
        -------
        dict[str, Any]
            Schema report dictionary with keys:
            - tables: List of table names
            - table_details: Dict mapping table names to their column metadata
            - relationships: List of foreign key relationships
            - indexes: Dict mapping table names to their index metadata

        Raises
        ------
        RuntimeError
            If not connected to database.
        """
        if not self.engine:
            msg = "Not connected to database. Call connect() first."
            raise RuntimeError(msg)

        try:
            tables = self.inspect_tables()
            table_details: dict[str, list[dict[str, Any]]] = {}
            indexes: dict[str, list[dict[str, Any]]] = {}

            for table_name in tables:
                table_details[table_name] = self.inspect_columns(table_name)
                indexes[table_name] = self.inspect_indexes(table_name)

            relationships = self.inspect_relationships()

            report = {
                "tables": tables,
                "table_details": table_details,
                "relationships": relationships,
                "indexes": indexes,
            }

        except SQLAlchemyError as e:
            logger.error(f"Failed to generate schema report: {e}")
            raise
        else:
            logger.info("Generated schema report")
            return report
