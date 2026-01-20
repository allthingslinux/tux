"""
Schema validation for migration compatibility.

Validates the old database schema report against expected mappings
to identify potential migration issues before execution.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from .mapper import ModelMapper
from .migrator import MIGRATION_ORDER


class SchemaValidator:
    """
    Validate old database schema against expected migration mappings.

    Checks for compatibility issues, missing fields, primary key mismatches,
    and other potential problems before migration execution.
    """

    def __init__(self, mapper: ModelMapper) -> None:
        """
        Initialize schema validator.

        Parameters
        ----------
        mapper : ModelMapper
            Model mapper instance.
        """
        self.mapper = mapper

        # Expected primary key configurations
        # Format: {old_table_name: [list of PK column names]}
        self.expected_pks: dict[str, list[str]] = {
            "Guild": ["guild_id"],
            "GuildConfig": ["guild_id"],
            "Case": ["case_id"],
            "Snippet": ["snippet_id"],
            "Reminder": ["reminder_id"],
            "AFKModel": ["member_id", "guild_id"],  # Composite PK
            "Levels": ["member_id", "guild_id"],  # Composite PK
            "Starboard": ["guild_id"],
            "StarboardMessage": ["message_id"],
            "Note": ["note_id"],  # Not migrated but exists in old DB
        }

        # Required fields for each table (fields that must exist)
        # Note: created_at/updated_at are added by BaseModel but come from old DB
        # They're not required in old schema but will exist in new schema
        self.required_fields: dict[str, list[str]] = {
            "Guild": ["guild_id", "guild_joined_at", "case_count"],
            "GuildConfig": ["guild_id"],
            "Case": [
                "case_id",
                "case_type",
                "case_reason",
                "case_moderator_id",
                "case_user_id",
                "guild_id",
            ],
            "Snippet": [
                "snippet_id",
                "snippet_name",
                "snippet_user_id",
                "guild_id",
            ],
            "Reminder": [
                "reminder_id",
                "reminder_content",
                "reminder_expires_at",
                "reminder_channel_id",
                "reminder_user_id",
                "guild_id",
            ],
            "AFKModel": [
                "member_id",
                "guild_id",
                "nickname",
                "reason",
                "since",
                # Note: created_at/updated_at added by BaseModel in new schema
            ],
            "Levels": [
                "member_id",
                "guild_id",
                "xp",
                "level",
                # Note: created_at/updated_at added by BaseModel in new schema
            ],
            "Starboard": [
                "guild_id",
                "starboard_channel_id",
                "starboard_emoji",
                "starboard_threshold",
                # Note: created_at/updated_at added by BaseModel in new schema
            ],
            "StarboardMessage": [
                "message_id",
                "message_content",
                "message_channel_id",
                "message_user_id",
                "message_guild_id",
                "star_count",
                "starboard_message_id",
                # Note: created_at/updated_at added by BaseModel in new schema
            ],
        }

    def validate_schema_report(self, schema_report: dict[str, Any]) -> dict[str, Any]:
        """
        Validate schema report against expected mappings.

        Parameters
        ----------
        schema_report : dict[str, Any]
            Schema report from SchemaInspector.

        Returns
        -------
        dict[str, Any]
            Validation results with keys:
            - valid: bool
            - issues: list[dict[str, Any]]
            - warnings: list[dict[str, Any]]
            - summary: dict[str, Any]
        """
        logger.info("Validating schema report")

        issues: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        tables = schema_report.get("tables", [])
        table_details = schema_report.get("table_details", {})

        # Validate each table
        for old_table_name in tables:
            if old_table_name not in table_details:
                issues.append(
                    {
                        "type": "missing_table_details",
                        "table": old_table_name,
                        "severity": "error",
                        "message": f"Table '{old_table_name}' listed but no details found",
                    },
                )
                continue

            columns = table_details[old_table_name]
            column_names = {col["name"] for col in columns}

            # Check primary key configuration
            pk_issues = self._validate_primary_keys(old_table_name, columns)
            issues.extend(pk_issues)

            # Check required fields
            field_issues = self._validate_required_fields(old_table_name, column_names)
            issues.extend(field_issues)

            # Check field mappings
            mapping_warnings = self._validate_field_mappings(old_table_name, columns)
            warnings.extend(mapping_warnings)

        # Validate relationships
        relationship_issues = self._validate_relationships(schema_report)
        issues.extend(relationship_issues)

        # Summary
        error_count = len([i for i in issues if i["severity"] == "error"])
        warning_count = len(warnings) + len(
            [i for i in issues if i["severity"] == "warning"],
        )

        summary = {
            "total_tables": len(tables),
            "errors": error_count,
            "warnings": warning_count,
            "valid": error_count == 0,
        }

        logger.info(
            f"Schema validation complete: {error_count} errors, {warning_count} warnings",
        )

        return {
            "valid": error_count == 0,
            "issues": issues,
            "warnings": warnings,
            "summary": summary,
        }

    def _validate_primary_keys(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Validate primary key configuration.

        Parameters
        ----------
        table_name : str
            Table name.
        columns : list[dict[str, Any]]
            Column metadata.

        Returns
        -------
        list[dict[str, Any]]
            List of issues found.
        """
        issues: list[dict[str, Any]] = []

        if table_name not in self.expected_pks:
            # Table not in migration order (e.g., Note)
            return issues

        expected_pk_cols = set(self.expected_pks[table_name])
        actual_pk_cols = {
            col["name"] for col in columns if col.get("primary_key", False)
        }

        if expected_pk_cols != actual_pk_cols:
            severity = (
                "error" if len(expected_pk_cols) > len(actual_pk_cols) else "warning"
            )
            issues.append(
                {
                    "type": "primary_key_mismatch",
                    "table": table_name,
                    "severity": severity,
                    "expected": list(expected_pk_cols),
                    "actual": list(actual_pk_cols),
                    "message": (
                        f"Primary key mismatch for '{table_name}': "
                        f"expected {list(expected_pk_cols)}, found {list(actual_pk_cols)}"
                    ),
                },
            )

        return issues

    def _validate_required_fields(
        self,
        table_name: str,
        column_names: set[str],
    ) -> list[dict[str, Any]]:
        """
        Validate required fields exist.

        Parameters
        ----------
        table_name : str
            Table name.
        column_names : set[str]
            Set of column names in table.

        Returns
        -------
        list[dict[str, Any]]
            List of issues found.
        """
        issues: list[dict[str, Any]] = []

        if table_name not in self.required_fields:
            return issues

        required = set(self.required_fields[table_name])
        missing = required - column_names

        if missing:
            issues.append(
                {
                    "type": "missing_required_fields",
                    "table": table_name,
                    "severity": "error",
                    "missing_fields": list(missing),
                    "message": (
                        f"Missing required fields in '{table_name}': {list(missing)}"
                    ),
                },
            )

        return issues

    def _validate_field_mappings(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Validate field mappings exist in mapper.

        Parameters
        ----------
        table_name : str
            Table name.
        columns : list[dict[str, Any]]
            Column metadata.

        Returns
        -------
        list[dict[str, Any]]
            List of warnings found.
        """
        warnings: list[dict[str, Any]] = []

        # Check if table is in migration order
        if not any(old_name == table_name for old_name, _ in MIGRATION_ORDER):
            return warnings

        # Get field mappings for this table
        field_mappings = self.mapper.field_mappings.get(table_name, {})
        column_names = {col["name"] for col in columns}

        # Check for unmapped columns (not critical, but worth noting)
        unmapped = column_names - set(field_mappings.keys())
        deprecated_fields: dict[str, list[str]] = {
            "GuildConfig": [
                "base_member_role_id",
                "base_staff_role_id",
                "general_channel_id",
                "quarantine_role_id",
                "starboard_channel_id",
            ],
        }

        for col_name in unmapped:
            if (
                table_name in deprecated_fields
                and col_name in deprecated_fields[table_name]
            ):
                continue  # Known deprecated field
            if col_name.startswith("perm_level_") and col_name.endswith("_role_id"):
                continue  # Handled separately via migrate_permission_ranks()

            warnings.append(
                {
                    "type": "unmapped_field",
                    "table": table_name,
                    "field": col_name,
                    "severity": "warning",
                    "message": (
                        f"Field '{col_name}' in '{table_name}' is not mapped "
                        "(may be deprecated or handled separately)"
                    ),
                },
            )

        return warnings

    def _validate_relationships(
        self,
        schema_report: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Validate foreign key relationships.

        Parameters
        ----------
        schema_report : dict[str, Any]
            Schema report.

        Returns
        -------
        list[dict[str, Any]]
            List of issues found.
        """
        issues: list[dict[str, Any]] = []

        relationships = schema_report.get("relationships", [])
        tables = schema_report.get("tables", [])

        # Check that all relationships point to existing tables
        for rel in relationships:
            referred_table = rel.get("referred_table")
            if referred_table not in tables:
                issues.append(
                    {
                        "type": "invalid_foreign_key",
                        "table": rel.get("table"),
                        "severity": "error",
                        "referred_table": referred_table,
                        "message": (
                            f"Foreign key in '{rel.get('table')}' references "
                            f"non-existent table '{referred_table}'"
                        ),
                    },
                )

        # Check that Guild table exists (most FKs point to it)
        if "Guild" not in tables:
            issues.append(
                {
                    "type": "missing_critical_table",
                    "table": "Guild",
                    "severity": "error",
                    "message": (
                        "Guild table not found - required for foreign key relationships"
                    ),
                },
            )

        return issues
