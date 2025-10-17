"""
Dynamic permission system controllers.

Provides database operations for the flexible permission system that allows
servers to customize their permission levels and role assignments.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from tux.database.controllers.base import BaseController
from tux.database.models.models import (
    GuildCommandPermission,
    GuildPermissionAssignment,
    GuildPermissionRank,
)

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class GuildPermissionRankController(BaseController[GuildPermissionRank]):
    """Controller for managing guild permission ranks."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildPermissionRank, db)

    async def create_permission_rank(
        self,
        guild_id: int,
        rank: int,
        name: str,
        description: str | None = None,
    ) -> GuildPermissionRank:
        """Create a new permission rank for a guild."""
        return await self.create(
            guild_id=guild_id,
            rank=rank,
            name=name,
            description=description,
        )

    async def get_permission_ranks_by_guild(self, guild_id: int) -> list[GuildPermissionRank]:
        """Get all permission ranks for a guild."""
        return await self.find_all(
            filters=GuildPermissionRank.guild_id == guild_id,
            order_by=GuildPermissionRank.rank,
        )

    async def get_permission_rank(self, guild_id: int, rank: int) -> GuildPermissionRank | None:
        """Get a specific permission rank."""
        return await self.find_one(
            filters=(GuildPermissionRank.guild_id == guild_id) & (GuildPermissionRank.rank == rank),
        )

    async def update_permission_rank(
        self,
        guild_id: int,
        rank: int,
        name: str | None = None,
        description: str | None = None,
    ) -> GuildPermissionRank | None:
        """Update a permission rank."""
        # Find the record first
        record = await self.find_one(
            filters=(GuildPermissionRank.guild_id == guild_id) & (GuildPermissionRank.rank == rank),
        )
        if not record:
            return None

        # Update the record
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        update_data["updated_at"] = datetime.now(UTC)

        return await self.update_by_id(record.id, **update_data)

    async def delete_permission_rank(self, guild_id: int, rank: int) -> bool:
        """Delete a permission rank."""
        deleted_count = await self.delete_where(
            filters=(GuildPermissionRank.guild_id == guild_id) & (GuildPermissionRank.rank == rank),
        )
        return deleted_count > 0


class GuildPermissionAssignmentController(BaseController[GuildPermissionAssignment]):
    """Controller for managing guild permission assignments."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the guild permission assignment controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(GuildPermissionAssignment, db)

    async def assign_permission_rank(
        self,
        guild_id: int,
        permission_rank_id: int,
        role_id: int,
        assigned_by: int,
    ) -> GuildPermissionAssignment:
        """Assign a permission level to a role."""
        return await self.create(
            guild_id=guild_id,
            permission_rank_id=permission_rank_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

    async def get_assignments_by_guild(self, guild_id: int) -> list[GuildPermissionAssignment]:
        """Get all permission assignments for a guild."""
        return await self.find_all(filters=GuildPermissionAssignment.guild_id == guild_id)

    async def remove_role_assignment(self, guild_id: int, role_id: int) -> bool:
        """Remove a permission level assignment from a role."""
        deleted_count = await self.delete_where(
            filters=(GuildPermissionAssignment.guild_id == guild_id) & (GuildPermissionAssignment.role_id == role_id),
        )
        return deleted_count > 0

    async def get_user_permission_rank(self, guild_id: int, user_id: int, user_roles: list[int]) -> int:
        """Get the highest permission rank a user has based on their roles."""
        if not user_roles:
            return 0

        # Get all permission assignments for this guild
        assignments = await self.get_assignments_by_guild(guild_id)
        if not assignments:
            return 0

        # Find the highest rank the user has access to
        max_rank = 0
        assigned_role_ids = {assignment.role_id for assignment in assignments}

        # Check if user has any of the assigned roles
        user_assigned_roles = set(user_roles) & assigned_role_ids
        if not user_assigned_roles:
            return 0

        # Get the permission levels for the user's roles
        # We need to query the permission level IDs
        permission_rank_ids = {
            assignment.permission_rank_id for assignment in assignments if assignment.role_id in user_assigned_roles
        }

        if not permission_rank_ids:
            return 0

        # Query permission levels to get their numeric rank values

        rank_controller = BaseController(GuildPermissionRank, self.db)

        for level_id in permission_rank_ids:
            rank_record = await rank_controller.get_by_id(level_id)
            if rank_record and rank_record.rank > max_rank:
                max_rank = int(rank_record.rank)

        return max_rank


class GuildCommandPermissionController(BaseController[GuildCommandPermission]):
    """Controller for managing command permission requirements."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the guild command permission controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(GuildCommandPermission, db)

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_rank: int,
        category: str | None = None,
        description: str | None = None,
    ) -> GuildCommandPermission:  # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
        """Set the permission rank required for a command."""
        result = await self.upsert(
            filters={"guild_id": guild_id, "command_name": command_name},
            guild_id=guild_id,
            command_name=command_name,
            required_rank=required_rank,
            category=category,
            description=description,
        )
        return result[0]  # upsert returns (record, created)

    async def get_command_permission(self, guild_id: int, command_name: str) -> GuildCommandPermission | None:
        """Get the permission requirement for a specific command."""
        return await self.find_one(
            filters=(GuildCommandPermission.guild_id == guild_id)
            & (GuildCommandPermission.command_name == command_name),
        )

    async def get_commands_by_category(self, guild_id: int, category: str) -> list[GuildCommandPermission]:
        """Get all commands in a specific category."""
        return await self.find_all(
            filters=(GuildCommandPermission.guild_id == guild_id) & (GuildCommandPermission.category == category),
        )

    async def get_all_command_permissions(self, guild_id: int) -> list[GuildCommandPermission]:
        """Get all command permissions for a guild."""
        return await self.find_all(
            filters=GuildCommandPermission.guild_id == guild_id,
            order_by=(GuildCommandPermission.category, GuildCommandPermission.command_name),
        )
