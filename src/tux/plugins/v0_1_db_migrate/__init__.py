"""Database migration plugin for migrating from Prisma to SQLModel.

This plugin provides tools to migrate data from the old Prisma/Supabase database
(pre v0.1.0) to the new SQLModel/PostgreSQL database (v0.1.0+).

Components:
- SchemaInspector: Inspect old database schema
- ModelMapper: Map Prisma models to SQLModel models
- DataExtractor: Extract and transform data in batches
- DatabaseMigrator: Execute migrations with transaction support
- MigrationValidator: Validate migrated data
"""

from .config import MigrationConfig
from .extractor import DataExtractor
from .mapper import ModelMapper
from .migrator import MIGRATION_ORDER, DatabaseMigrator
from .plugin import DatabaseMigration, setup
from .schema_inspector import SchemaInspector
from .utils import (
    convert_prisma_to_sqlmodel_name,
    normalize_datetime,
    safe_json_parse,
    sanitize_database_url,
    transform_enum_value,
)
from .validator import MigrationValidator

__all__ = [
    "MigrationConfig",
    "SchemaInspector",
    "ModelMapper",
    "DataExtractor",
    "DatabaseMigrator",
    "MigrationValidator",
    "DatabaseMigration",
    "setup",
    "MIGRATION_ORDER",
    # Utilities
    "convert_prisma_to_sqlmodel_name",
    "normalize_datetime",
    "safe_json_parse",
    "sanitize_database_url",
    "transform_enum_value",
]
