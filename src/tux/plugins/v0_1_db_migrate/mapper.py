"""
Model mapper for Prisma to SQLModel conversion.

Maps old Prisma model structures to new SQLModel models,
handling field name changes, type conversions, and defaults.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from loguru import logger

from tux.database.models import (
    AFK,
    Case,
    CaseType,
    Guild,
    GuildConfig,
    Levels,
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
)

from .utils import (
    convert_prisma_to_sqlmodel_name,
    normalize_datetime,
    safe_json_parse,
    transform_enum_value,
)

# CaseType enum mapping (Prisma -> SQLModel)
# Note: SQLModel CaseType enum uses uppercase values
CASE_TYPE_MAPPING: dict[str, str] = {
    "BAN": "BAN",
    "KICK": "KICK",
    "WARN": "WARN",
    "TIMEOUT": "TIMEOUT",
    "JAIL": "JAIL",
    "UNBAN": "UNBAN",
    "UNTIMEOUT": "UNTIMEOUT",
    "UNJAIL": "UNJAIL",
    "TEMPBAN": "TEMPBAN",
    "HACKBAN": "HACKBAN",
    "SNIPPETBAN": "SNIPPETBAN",
    "SNIPPETUNBAN": "SNIPPETUNBAN",
    "POLLBAN": "POLLBAN",
    "POLLUNBAN": "POLLUNBAN",
}


class ModelMapper:
    """
    Map old Prisma models to new SQLModel models.

    Handles field name conversion, type transformation, and
    default value assignment for migrated data.

    Attributes
    ----------
    field_mappings : dict[str, dict[str, str]]
        Mapping from old table names to field name mappings.
    """

    def __init__(self) -> None:
        """Initialize model mapper with field mappings."""
        # Define field mappings for each table
        # Format: {old_db_column_name: new_model_field_name}
        # Note: Old DB uses snake_case column names directly
        self.field_mappings: dict[str, dict[str, str]] = {
            "Guild": {
                "guild_id": "id",  # Old DB PK -> New model PK
                "guild_joined_at": "guild_joined_at",
                "case_count": "case_count",
                # Note: Old DB doesn't have created_at/updated_at
            },
            "GuildConfig": {
                "guild_id": "id",  # Old DB PK/FK -> New model PK/FK
                "prefix": "prefix",
                "mod_log_id": "mod_log_id",
                "audit_log_id": "audit_log_id",
                "join_log_id": "join_log_id",
                "private_log_id": "private_log_id",
                "report_log_id": "report_log_id",
                "dev_log_id": "dev_log_id",
                "jail_channel_id": "jail_channel_id",
                "jail_role_id": "jail_role_id",
                # Note: Old DB has perm_level_*_role_id fields that new model doesn't have
                # Note: Old DB doesn't have onboarding_completed/onboarding_stage
                # Note: Old DB doesn't have created_at/updated_at
            },
            "Case": {
                "case_id": "id",  # Old DB PK -> New model PK
                "case_status": "case_status",
                "case_type": "case_type",
                "case_reason": "case_reason",
                "case_moderator_id": "case_moderator_id",
                "case_user_id": "case_user_id",
                "case_user_roles": "case_user_roles",
                "case_number": "case_number",
                "case_expires_at": "case_expires_at",
                "case_tempban_expired": "case_processed",  # Map old field to new field name
                "guild_id": "guild_id",
                "case_created_at": "created_at",  # Map old created_at to new created_at
                # Note: New model has case_metadata, mod_log_message_id
                #       which old DB doesn't have (will use defaults)
            },
            "Snippet": {
                "snippet_id": "id",  # Old DB PK -> New model PK
                "snippet_name": "snippet_name",
                "snippet_content": "snippet_content",
                "snippet_user_id": "snippet_user_id",
                "guild_id": "guild_id",
                "uses": "uses",
                "locked": "locked",
                "alias": "alias",
                "snippet_created_at": "created_at",  # TimestampMixin
            },
            "Reminder": {
                "reminder_id": "id",  # Old DB PK -> New model PK
                "reminder_content": "reminder_content",
                "reminder_expires_at": "reminder_expires_at",
                "reminder_channel_id": "reminder_channel_id",
                "reminder_user_id": "reminder_user_id",
                "reminder_sent": "reminder_sent",
                "guild_id": "guild_id",
                "reminder_created_at": "created_at",  # TimestampMixin
            },
            "AFKModel": {  # Note: Old DB table is "AFKModel", not "AFK"
                "member_id": "member_id",  # Composite PK part 1
                "guild_id": "guild_id",  # Composite PK part 2
                "nickname": "nickname",
                "reason": "reason",
                "since": "since",
                "until": "until",
                "enforced": "enforced",
                "perm_afk": "perm_afk",
            },
            "Levels": {
                "member_id": "member_id",  # Composite PK part 1
                "guild_id": "guild_id",  # Composite PK part 2
                "xp": "xp",
                "level": "level",
                "blacklisted": "blacklisted",
                "last_message": "last_message",
            },
            "Starboard": {
                "guild_id": "id",  # Old DB PK -> New model PK
                "starboard_channel_id": "starboard_channel_id",
                "starboard_emoji": "starboard_emoji",
                "starboard_threshold": "starboard_threshold",
            },
            "StarboardMessage": {
                "message_id": "id",  # Old DB PK -> New model PK
                "message_content": "message_content",
                "message_expires_at": "message_expires_at",
                "message_channel_id": "message_channel_id",
                "message_user_id": "message_user_id",
                "message_guild_id": "message_guild_id",  # Model keeps this name (FK to guild.id)
                "star_count": "star_count",
                "starboard_message_id": "starboard_message_id",
                "message_created_at": "created_at",  # TimestampMixin
            },
            # Note: PermissionRank, PermissionAssignment, PermissionCommand tables
            # don't exist in old DB - they're new features
        }

    def get_table_mapping(self, old_table_name: str) -> str:
        """
        Get new table name for old Prisma table name.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name (e.g., "Guild", "Case").

        Returns
        -------
        str
            New SQLModel table name (e.g., "guild", "cases").

        Notes
        -----
        Table name mappings:
        - Guild -> guild
        - GuildConfig -> guild_config
        - Case -> cases
        - Snippet -> snippet
        - Reminder -> reminder
        - AFK -> afk
        - Levels -> levels
        - Starboard -> starboard
        - StarboardMessage -> starboard_message
        - PermissionRank -> permission_ranks
        - PermissionAssignment -> permission_assignments
        - PermissionCommand -> permission_commands
        """
        table_mappings: dict[str, str] = {
            "Guild": "guild",
            "GuildConfig": "guild_config",
            "Case": "cases",
            "Snippet": "snippet",
            "Reminder": "reminder",
            "AFKModel": "afk",  # Old DB table is "AFKModel"
            "Levels": "levels",
            "Starboard": "starboard",
            "StarboardMessage": "starboard_message",
            # Note: PermissionRank, PermissionAssignment, PermissionCommand
            # don't exist in old DB - they're new features
        }

        # Try exact match first
        if old_table_name in table_mappings:
            return table_mappings[old_table_name]

        # Try converting Prisma name to SQLModel name
        converted = convert_prisma_to_sqlmodel_name(old_table_name)
        if converted in table_mappings.values():
            return converted

        # Fallback: convert to snake_case
        logger.warning(
            f"Unknown table mapping for '{old_table_name}', using converted name: {converted}",
        )
        return converted

    def get_field_mapping(self, old_table_name: str, old_field_name: str) -> str:
        """
        Get new field name for old Prisma field name.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.
        old_field_name : str
            Old Prisma field name.

        Returns
        -------
        str
            New SQLModel field name.
        """
        # Try exact table match
        if (
            old_table_name in self.field_mappings
            and old_field_name in self.field_mappings[old_table_name]
        ):
            return self.field_mappings[old_table_name][old_field_name]

        # Try converting field name
        converted = convert_prisma_to_sqlmodel_name(old_field_name)
        logger.debug(
            f"Field '{old_field_name}' in table '{old_table_name}' mapped to '{converted}'",
        )
        return converted

    def transform_row(
        self,
        old_table_name: str,
        old_row: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform a row from old Prisma format to new SQLModel format.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.
        old_row : dict[str, Any]
            Row data from old database.

        Returns
        -------
        dict[str, Any]
            Transformed row data for new database.

        Notes
        -----
        Handles:
        - Field name conversion
        - Type transformations (enums, JSON, datetime)
        - Default values for new required fields
        - Removal of deprecated fields
        - Validation of required constraints (e.g., guild_id > 0)
        """
        # Validate Guild table: guild_id must be > 0 (check constraint)
        if old_table_name == "Guild":
            guild_id = old_row.get("guild_id")
            if guild_id is not None and guild_id <= 0:
                logger.warning(
                    f"Skipping invalid Guild row with guild_id={guild_id} "
                    "(must be > 0 per check constraint)",
                )
                return {}  # Return empty dict to skip this row

        new_row: dict[str, Any] = {}
        field_mapping = self.field_mappings.get(old_table_name, {})

        for old_field, old_value in old_row.items():
            # Get new field name
            new_field = field_mapping.get(
                old_field,
                old_field,  # If not mapped, use same name (already snake_case)
            )

            # Skip None values (will use defaults if required)
            if old_value is None:
                continue

            # Skip deprecated fields that don't exist in new model
            # Note: perm_level_*_role_id fields are migrated separately via migrate_permission_ranks()
            # Note: case_tempban_expired is now mapped to case_processed, not deprecated
            deprecated_fields: dict[str, list[str]] = {
                "GuildConfig": [
                    "base_member_role_id",
                    "base_staff_role_id",
                    "general_channel_id",
                    "quarantine_role_id",
                    "starboard_channel_id",
                    # Note: perm_level_*_role_id fields are handled separately
                    # They're skipped here but migrated to PermissionRank/PermissionAssignment
                ],
            }
            if (
                old_table_name in deprecated_fields
                and old_field in deprecated_fields[old_table_name]
            ):
                logger.debug(
                    f"Skipping deprecated field '{old_field}' from table '{old_table_name}'",
                )
                continue

            # Transform value based on field type
            transformed_value = self._transform_value(
                old_table_name,
                old_field,
                new_field,
                old_value,
            )

            if transformed_value is not None:
                new_row[new_field] = transformed_value

        return new_row

    def _transform_value(  # noqa: PLR0911
        self,
        old_table_name: str,
        old_field: str,
        new_field: str,
        old_value: Any,
    ) -> Any:
        """
        Transform a single field value.

        Parameters
        ----------
        old_table_name : str
            Old Prisma table name.
        old_field : str
            Old field name.
        new_field : str
            New field name.
        old_value : Any
            Old field value.

        Returns
        -------
        Any
            Transformed field value.
        """
        # Handle enum fields
        if old_table_name == "Case" and old_field == "case_type":
            # CaseType enum uses uppercase values
            transformed = transform_enum_value(old_value, CASE_TYPE_MAPPING, "BAN")
            # Convert to CaseType enum if needed
            if isinstance(transformed, str):
                with suppress(ValueError):
                    transformed = CaseType(transformed)
            return transformed

        # Handle JSON fields
        if "metadata" in new_field.lower() or "roles" in new_field.lower():
            return safe_json_parse(old_value)

        # Handle datetime fields
        # Check for specific datetime-related field names
        new_field_lower = new_field.lower()
        if (
            new_field_lower.endswith(("_at", "_since", "_until"))
            or "_at_" in new_field_lower
            or "_since_" in new_field_lower
            or "_until_" in new_field_lower
        ):
            return normalize_datetime(old_value)

        # Handle boolean fields
        if isinstance(old_value, bool):
            return old_value

        # Handle numeric fields
        if isinstance(old_value, (int, float)):
            return old_value

        # Handle string fields
        if isinstance(old_value, str):
            return old_value

        # Default: return as-is
        return old_value

    def get_model_class(self, table_name: str) -> type[Any]:
        """
        Get SQLModel class for a table name.

        Parameters
        ----------
        table_name : str
            New SQLModel table name.

        Returns
        -------
        type[Any]
            SQLModel model class.

        Raises
        ------
        ValueError
            If table name is not recognized.
        """
        model_map: dict[str, type[Any]] = {
            "guild": Guild,
            "guild_config": GuildConfig,
            "cases": Case,
            "snippet": Snippet,
            "reminder": Reminder,
            "afk": AFK,
            "levels": Levels,
            "starboard": Starboard,
            "starboard_message": StarboardMessage,
            "permission_ranks": PermissionRank,
            "permission_assignments": PermissionAssignment,
            "permission_commands": PermissionCommand,
        }

        if table_name not in model_map:
            msg = f"Unknown table name: {table_name}"
            raise ValueError(msg)

        return model_map[table_name]
