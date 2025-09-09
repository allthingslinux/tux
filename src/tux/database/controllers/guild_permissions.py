"""
Dynamic permission system controllers.

Provides database operations for the flexible permission system that allows
servers to customize their permission levels and role assignments.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import delete, func, select, update

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

    def __init__(self, db: DatabaseService) -> None:
        super().__init__(model=GuildPermissionLevel, db=db)

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
        async with self.db.session() as session:
            permission_level = GuildPermissionLevel(
                guild_id=guild_id,
                level=level,
                name=name,
                description=description,
                color=color,
                position=position,
            )
            session.add(permission_level)
            await session.commit()
            await session.refresh(permission_level)
            return permission_level

    async def get_permission_levels_by_guild(self, guild_id: int) -> list[GuildPermissionLevel]:
        """Get all permission levels for a guild."""
        async with self.db.session() as session:
            statement = (  # pyright: ignore[union-attr]
                select(GuildPermissionLevel)
                .where(
                    GuildPermissionLevel.guild_id == guild_id,  # type: ignore[arg-type]
                )
                .where(
                    GuildPermissionLevel.enabled,  # type: ignore[arg-type]
                )
                .order_by(GuildPermissionLevel.position, GuildPermissionLevel.level)  # type: ignore[arg-type]
            )

            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_permission_level(self, guild_id: int, level: int) -> GuildPermissionLevel | None:
        """Get a specific permission level."""
        async with self.db.session() as session:
            statement = select(GuildPermissionLevel).where(
                GuildPermissionLevel.guild_id == guild_id,  # type: ignore[arg-type]
                GuildPermissionLevel.level == level,  # type: ignore[arg-type]
                GuildPermissionLevel.enabled,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return result.scalar_one_or_none()

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
        async with self.db.session() as session:
            statement = (  # pyright: ignore[assignment]
                update(GuildPermissionLevel)
                .where(
                    GuildPermissionLevel.guild_id == guild_id,  # type: ignore[arg-type]
                    GuildPermissionLevel.level == level,  # type: ignore[arg-type]
                )
                .values(name=name, description=description, color=color, position=position, updated_at=func.now())
                .returning(GuildPermissionLevel)
            )

            result = await session.execute(statement)
            updated = result.scalar_one_or_none()
            if updated:
                await session.commit()
            return updated

    async def delete_permission_level(self, guild_id: int, level: int) -> bool:
        """Delete a permission level."""
        async with self.db.session() as session:
            statement = delete(GuildPermissionLevel).where(
                GuildPermissionLevel.guild_id == guild_id,  # type: ignore[arg-type]
                GuildPermissionLevel.level == level,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            await session.commit()
            return result.rowcount > 0


class GuildPermissionAssignmentController(BaseController[GuildPermissionAssignment]):
    """Controller for managing permission level assignments to roles."""

    def __init__(self, db: DatabaseService) -> None:
        super().__init__(model=GuildPermissionAssignment, db=db)

    async def assign_permission_level(
        self,
        guild_id: int,
        permission_level_id: int,
        role_id: int,
        assigned_by: int,
    ) -> GuildPermissionAssignment:
        """Assign a permission level to a role."""
        async with self.db.session() as session:
            assignment = GuildPermissionAssignment(
                guild_id=guild_id,
                permission_level_id=permission_level_id,
                role_id=role_id,
                assigned_by=assigned_by,
            )
            session.add(assignment)
            await session.commit()
            await session.refresh(assignment)
            return assignment

    async def get_assignments_by_guild(self, guild_id: int) -> list[GuildPermissionAssignment]:
        """Get all permission assignments for a guild."""
        async with self.db.session() as session:
            statement = select(GuildPermissionAssignment).where(
                GuildPermissionAssignment.guild_id == guild_id,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_user_permission_level(self, guild_id: int, user_id: int, user_roles: list[int]) -> int:
        """Get the highest permission level a user has based on their roles."""
        if not user_roles:
            return 0

        async with self.db.session() as session:
            # Get all permission assignments for this guild
            assignments = await self.get_assignments_by_guild(guild_id)
            if not assignments:
                return 0

            # Find the highest level the user has access to
            max_level = cast(int, 0)
            assigned_role_ids = {assignment.role_id for assignment in assignments}

            # Check if user has any of the assigned roles
            user_assigned_roles = set(user_roles) & assigned_role_ids
            if not user_assigned_roles:
                return 0

            # Get the permission levels for the user's roles
            for assignment in assignments:
                if assignment.role_id in user_assigned_roles:
                    # Get the permission level details
                    level_info = await session.execute(  # type: ignore[assignment]
                        select(GuildPermissionLevel.level).where(  # type: ignore[arg-type]
                            GuildPermissionLevel.id == assignment.permission_level_id,  # type: ignore[arg-type]
                            GuildPermissionLevel.enabled,  # type: ignore[arg-type]
                        ),
                    )
                    level = cast(int | None, level_info.scalar_one_or_none())
                    if level is not None and level > max_level:
                        max_level = level

            return max_level

    async def remove_role_assignment(self, guild_id: int, role_id: int) -> bool:
        """Remove a permission level assignment from a role."""
        async with self.db.session() as session:
            statement = delete(GuildPermissionAssignment).where(
                GuildPermissionAssignment.guild_id == guild_id,  # type: ignore[arg-type]
                GuildPermissionAssignment.role_id == role_id,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            await session.commit()
            return result.rowcount > 0


class GuildCommandPermissionController(BaseController[GuildCommandPermission]):
    """Controller for managing command permission requirements."""

    def __init__(self, db: DatabaseService) -> None:
        super().__init__(model=GuildCommandPermission, db=db)

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_level: int,
        category: str | None = None,
        description: str | None = None,
    ) -> GuildCommandPermission:  # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
        """Set the permission level required for a command."""
        async with self.db.session() as session:
            # Check if it already exists
            existing = await self.get_command_permission(guild_id, command_name)
            if existing:
                # Update existing
                existing.required_level = required_level
                existing.category = category
                existing.description = description
                existing.updated_at = datetime.now(UTC)
                session.add(existing)
            else:
                # Create new
                existing = GuildCommandPermission(
                    guild_id=guild_id,
                    command_name=command_name,
                    required_level=required_level,
                    category=category,
                    description=description,
                )
                session.add(existing)

            await session.commit()
            await session.refresh(existing)
            return existing

    async def get_command_permission(self, guild_id: int, command_name: str) -> GuildCommandPermission | None:
        """Get the permission requirement for a specific command."""
        async with self.db.session() as session:
            statement = select(GuildCommandPermission).where(
                GuildCommandPermission.guild_id == guild_id,  # type: ignore[arg-type]
                GuildCommandPermission.command_name == command_name,  # type: ignore[arg-type]
                GuildCommandPermission.enabled,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return result.scalar_one_or_none()

    async def get_commands_by_category(self, guild_id: int, category: str) -> list[GuildCommandPermission]:
        """Get all commands in a specific category."""
        async with self.db.session() as session:
            statement = select(GuildCommandPermission).where(
                GuildCommandPermission.guild_id == guild_id,  # type: ignore[arg-type]
                GuildCommandPermission.category == category,  # type: ignore[arg-type]
                GuildCommandPermission.enabled,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_all_command_permissions(self, guild_id: int) -> list[GuildCommandPermission]:
        """Get all command permissions for a guild."""
        async with self.db.session() as session:
            statement = (  # pyright: ignore[union-attr]
                select(GuildCommandPermission)
                .where(
                    GuildCommandPermission.guild_id == guild_id,  # type: ignore[arg-type]
                )
                .where(
                    GuildCommandPermission.enabled,  # type: ignore[arg-type]
                )
                .order_by(GuildCommandPermission.category, GuildCommandPermission.command_name)  # type: ignore[arg-type]
            )

            result = await session.execute(statement)
            return list(result.scalars().all())


class GuildBlacklistController(BaseController[GuildBlacklist]):
    """Controller for managing blacklisted users, roles, and channels."""

    def __init__(self, db: DatabaseService) -> None:
        super().__init__(model=GuildBlacklist, db=db)

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
        async with self.db.session() as session:
            blacklist_entry = GuildBlacklist(
                guild_id=guild_id,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
                blacklisted_by=blacklisted_by,
                expires_at=expires_at,
            )
            session.add(blacklist_entry)
            await session.commit()
            await session.refresh(blacklist_entry)
            return blacklist_entry

    async def remove_from_blacklist(self, guild_id: int, target_type: str, target_id: int) -> bool:
        """Remove a target from the blacklist."""
        async with self.db.session() as session:
            statement = delete(GuildBlacklist).where(
                GuildBlacklist.guild_id == guild_id,  # type: ignore[arg-type]
                GuildBlacklist.target_type == target_type,  # type: ignore[arg-type]
                GuildBlacklist.target_id == target_id,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            await session.commit()
            return result.rowcount > 0

    async def is_blacklisted(self, guild_id: int, target_type: str, target_id: int) -> GuildBlacklist | None:
        """Check if a target is blacklisted."""
        async with self.db.session() as session:
            statement = (
                select(GuildBlacklist)
                .where(
                    GuildBlacklist.guild_id == guild_id,  # type: ignore[arg-type]
                    GuildBlacklist.target_type == target_type,  # type: ignore[arg-type]
                    GuildBlacklist.target_id == target_id,  # type: ignore[arg-type]
                )
                .where(
                    # Check if not expired
                    (GuildBlacklist.expires_at.is_(None)) | (GuildBlacklist.expires_at > func.now()),  # type: ignore[arg-type]
                )
            )
            result = await session.execute(statement)
            return result.scalar_one_or_none()

    async def get_guild_blacklist(self, guild_id: int) -> list[GuildBlacklist]:
        """Get all blacklist entries for a guild."""
        async with self.db.session() as session:
            statement = (
                select(GuildBlacklist)
                .where(
                    GuildBlacklist.guild_id == guild_id,  # type: ignore[arg-type]
                    # Include expired entries but mark them as such
                )
                .order_by(GuildBlacklist.blacklisted_at.desc())  # type: ignore[arg-type]
            )

            result = await session.execute(statement)
            return list(result.scalars().all())


class GuildWhitelistController(BaseController[GuildWhitelist]):
    """Controller for managing whitelisted users, roles, and channels."""

    def __init__(self, db: DatabaseService) -> None:
        super().__init__(model=GuildWhitelist, db=db)

    async def add_to_whitelist(
        self,
        guild_id: int,
        target_type: str,
        target_id: int,
        feature: str,
        whitelisted_by: int,
    ) -> GuildWhitelist:
        """Add a user, role, or channel to the whitelist for a specific feature."""
        async with self.db.session() as session:
            whitelist_entry = GuildWhitelist(
                guild_id=guild_id,
                target_type=target_type,
                target_id=target_id,
                feature=feature,
                whitelisted_by=whitelisted_by,
            )
            session.add(whitelist_entry)
            await session.commit()
            await session.refresh(whitelist_entry)
            return whitelist_entry

    async def remove_from_whitelist(self, guild_id: int, target_type: str, target_id: int, feature: str) -> bool:
        """Remove a target from the whitelist for a specific feature."""
        async with self.db.session() as session:
            statement = delete(GuildWhitelist).where(
                GuildWhitelist.guild_id == guild_id,  # type: ignore[arg-type]
                GuildWhitelist.target_type == target_type,  # type: ignore[arg-type]
                GuildWhitelist.target_id == target_id,  # type: ignore[arg-type]
                GuildWhitelist.feature == feature,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            await session.commit()
            return result.rowcount > 0

    async def is_whitelisted(self, guild_id: int, target_type: str, target_id: int, feature: str) -> bool:
        """Check if a target is whitelisted for a specific feature."""
        async with self.db.session() as session:
            statement = select(GuildWhitelist).where(
                GuildWhitelist.guild_id == guild_id,  # type: ignore[arg-type]
                GuildWhitelist.target_type == target_type,  # type: ignore[arg-type]
                GuildWhitelist.target_id == target_id,  # type: ignore[arg-type]
                GuildWhitelist.feature == feature,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return result.scalar_one_or_none() is not None

    async def get_whitelist_by_feature(self, guild_id: int, feature: str) -> list[GuildWhitelist]:
        """Get all whitelist entries for a specific feature in a guild."""
        async with self.db.session() as session:
            statement = select(GuildWhitelist).where(
                GuildWhitelist.guild_id == guild_id,  # type: ignore[arg-type]
                GuildWhitelist.feature == feature,  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return list(result.scalars().all())
