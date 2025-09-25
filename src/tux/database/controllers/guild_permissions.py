"""
Dynamic permission system controllers.

Provides database operations for the flexible permission system that allows
servers to customize their permission levels and role assignments.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, or_

from tux.database.controllers.base import BaseController
from tux.database.models.models import (
    GuildBlacklist,
    GuildCommandPermission,
    GuildPermissionAssignment,
    GuildPermissionLevel,
    GuildWhitelist,
)

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class GuildPermissionController(BaseController[GuildPermissionLevel]):
    """Controller for managing guild permission levels."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildPermissionLevel, db)

    async def create_permission_level(
        self,
        guild_id: int,
        level: int,
        name: str,
        description: str | None = None,
        color: int | None = None,
        position: int = 0,
    ) -> GuildPermissionLevel:
        """Create a new permission level for a guild."""
        return await self.create(
            guild_id=guild_id,
            level=level,
            name=name,
            description=description,
            color=color,
            position=position,
        )

    async def get_permission_levels_by_guild(self, guild_id: int) -> list[GuildPermissionLevel]:
        """Get all permission levels for a guild."""
        return await self.find_all(
            filters=(GuildPermissionLevel.guild_id == guild_id) & GuildPermissionLevel.enabled,
            order_by=[GuildPermissionLevel.position, GuildPermissionLevel.level],
        )

    async def get_permission_level(self, guild_id: int, level: int) -> GuildPermissionLevel | None:
        """Get a specific permission level."""
        return await self.find_one(
            filters=(GuildPermissionLevel.guild_id == guild_id)
            & (GuildPermissionLevel.level == level)
            & GuildPermissionLevel.enabled,
        )

    async def update_permission_level(
        self,
        guild_id: int,
        level: int,
        name: str | None = None,
        description: str | None = None,
        color: int | None = None,
        position: int | None = None,
    ) -> GuildPermissionLevel | None:
        """Update a permission level."""
        # Find the record first
        record = await self.find_one(
            filters=(GuildPermissionLevel.guild_id == guild_id) & (GuildPermissionLevel.level == level),
        )
        if not record:
            return None

        # Update the record
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if color is not None:
            update_data["color"] = color
        if position is not None:
            update_data["position"] = position
        update_data["updated_at"] = datetime.now(UTC)

        return await self.update_by_id(record.id, **update_data)

    async def delete_permission_level(self, guild_id: int, level: int) -> bool:
        """Delete a permission level."""
        deleted_count = await self.delete_where(
            filters=(GuildPermissionLevel.guild_id == guild_id) & (GuildPermissionLevel.level == level),
        )
        return deleted_count > 0


class GuildPermissionAssignmentController(BaseController[GuildPermissionAssignment]):
    """Controller for managing permission level assignments to roles."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildPermissionAssignment, db)

    async def assign_permission_level(
        self,
        guild_id: int,
        permission_level_id: int,
        role_id: int,
        assigned_by: int,
    ) -> GuildPermissionAssignment:
        """Assign a permission level to a role."""
        return await self.create(
            guild_id=guild_id,
            permission_level_id=permission_level_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

    async def get_assignments_by_guild(self, guild_id: int) -> list[GuildPermissionAssignment]:
        """Get all permission assignments for a guild."""
        return await self.find_all(filters=GuildPermissionAssignment.guild_id == guild_id)

    async def get_user_permission_level(self, guild_id: int, user_id: int, user_roles: list[int]) -> int:
        """Get the highest permission level a user has based on their roles."""
        if not user_roles:
            return 0

        # Get all permission assignments for this guild
        assignments = await self.get_assignments_by_guild(guild_id)
        if not assignments:
            return 0

        # Find the highest level the user has access to
        max_level = 0
        assigned_role_ids = {assignment.role_id for assignment in assignments}

        # Check if user has any of the assigned roles
        user_assigned_roles = set(user_roles) & assigned_role_ids
        if not user_assigned_roles:
            return 0

        # Get the permission levels for the user's roles
        for assignment in assignments:
            if assignment.role_id in user_assigned_roles:
                # Get the permission level details using BaseController
                level_record = await self.find_one(
                    filters=(GuildPermissionLevel.id == assignment.permission_level_id) & GuildPermissionLevel.enabled,
                )
                if level_record and level_record.level > max_level:  # type: ignore[misc]
                    max_level = int(level_record.level)  # type: ignore[arg-type]

        return max_level

    async def remove_role_assignment(self, guild_id: int, role_id: int) -> bool:
        """Remove a permission level assignment from a role."""
        deleted_count = await self.delete_where(
            filters=(GuildPermissionAssignment.guild_id == guild_id) & (GuildPermissionAssignment.role_id == role_id),
        )
        return deleted_count > 0


class GuildCommandPermissionController(BaseController[GuildCommandPermission]):
    """Controller for managing command permission requirements."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildCommandPermission, db)

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_level: int,
        category: str | None = None,
        description: str | None = None,
    ) -> GuildCommandPermission:  # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
        """Set the permission level required for a command."""
        result = await self.upsert(
            filters={"guild_id": guild_id, "command_name": command_name},
            guild_id=guild_id,
            command_name=command_name,
            required_level=required_level,
            category=category,
            description=description,
        )
        return result[0]  # upsert returns (record, created)

    async def get_command_permission(self, guild_id: int, command_name: str) -> GuildCommandPermission | None:
        """Get the permission requirement for a specific command."""
        return await self.find_one(
            filters=(GuildCommandPermission.guild_id == guild_id)
            & (GuildCommandPermission.command_name == command_name)
            & GuildCommandPermission.enabled,
        )

    async def get_commands_by_category(self, guild_id: int, category: str) -> list[GuildCommandPermission]:
        """Get all commands in a specific category."""
        return await self.find_all(
            filters=(GuildCommandPermission.guild_id == guild_id)
            & (GuildCommandPermission.category == category)
            & GuildCommandPermission.enabled,
        )

    async def get_all_command_permissions(self, guild_id: int) -> list[GuildCommandPermission]:
        """Get all command permissions for a guild."""
        return await self.find_all(
            filters=(GuildCommandPermission.guild_id == guild_id) & GuildCommandPermission.enabled,
            order_by=[GuildCommandPermission.category, GuildCommandPermission.command_name],
        )


class GuildBlacklistController(BaseController[GuildBlacklist]):
    """Controller for managing blacklisted users, roles, and channels."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildBlacklist, db)

    async def add_to_blacklist(
        self,
        guild_id: int,
        target_type: str,
        target_id: int,
        blacklisted_by: int,
        reason: str | None = None,
        expires_at: datetime | None = None,
    ) -> GuildBlacklist:
        """Add a user, role, or channel to the blacklist."""
        return await self.create(
            guild_id=guild_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            blacklisted_by=blacklisted_by,
            expires_at=expires_at,
        )

    async def remove_from_blacklist(self, guild_id: int, target_type: str, target_id: int) -> bool:
        """Remove a target from the blacklist."""
        deleted_count = await self.delete_where(
            filters=(GuildBlacklist.guild_id == guild_id)
            & (GuildBlacklist.target_type == target_type)
            & (GuildBlacklist.target_id == target_id),
        )
        return deleted_count > 0

    async def is_blacklisted(self, guild_id: int, target_type: str, target_id: int) -> GuildBlacklist | None:
        """Check if a target is blacklisted."""
        return await self.find_one(
            filters=(GuildBlacklist.guild_id == guild_id)
            & (GuildBlacklist.target_type == target_type)
            & (GuildBlacklist.target_id == target_id)
            & or_(GuildBlacklist.expires_at.is_(None), GuildBlacklist.expires_at > func.now()),  # type: ignore[reportUnknownMemberType]
        )

    async def get_guild_blacklist(self, guild_id: int) -> list[GuildBlacklist]:
        """Get all blacklist entries for a guild."""
        return await self.find_all(
            filters=GuildBlacklist.guild_id == guild_id,
            order_by=[GuildBlacklist.blacklisted_at.desc()],  # type: ignore[reportUnknownMemberType]
        )


class GuildWhitelistController(BaseController[GuildWhitelist]):
    """Controller for managing whitelisted users, roles, and channels."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildWhitelist, db)

    async def add_to_whitelist(
        self,
        guild_id: int,
        target_type: str,
        target_id: int,
        feature: str,
        whitelisted_by: int,
    ) -> GuildWhitelist:
        """Add a user, role, or channel to the whitelist for a specific feature."""
        return await self.create(
            guild_id=guild_id,
            target_type=target_type,
            target_id=target_id,
            feature=feature,
            whitelisted_by=whitelisted_by,
        )

    async def remove_from_whitelist(self, guild_id: int, target_type: str, target_id: int, feature: str) -> bool:
        """Remove a target from the whitelist for a specific feature."""
        deleted_count = await self.delete_where(
            filters=(GuildWhitelist.guild_id == guild_id)
            & (GuildWhitelist.target_type == target_type)
            & (GuildWhitelist.target_id == target_id)
            & (GuildWhitelist.feature == feature),
        )
        return deleted_count > 0

    async def is_whitelisted(self, guild_id: int, target_type: str, target_id: int, feature: str) -> bool:
        """Check if a target is whitelisted for a specific feature."""
        result = await self.find_one(
            filters=(GuildWhitelist.guild_id == guild_id)
            & (GuildWhitelist.target_type == target_type)
            & (GuildWhitelist.target_id == target_id)
            & (GuildWhitelist.feature == feature),
        )
        return result is not None

    async def get_whitelist_by_feature(self, guild_id: int, feature: str) -> list[GuildWhitelist]:
        """Get all whitelist entries for a specific feature in a guild."""
        return await self.find_all(filters=(GuildWhitelist.guild_id == guild_id) & (GuildWhitelist.feature == feature))
