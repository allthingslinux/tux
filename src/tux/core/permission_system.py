"""
Dynamic Permission System Service

This service provides a comprehensive, database-driven permission system that allows
servers to customize their permission ranks and role assignments. It's designed to be:

- Flexible: Each server can define their own permission hierarchy
- Scalable: Supports thousands of servers with different configurations
- Self-hosting friendly: Works with configuration files or commands
- Developer-friendly: Clean API for easy integration
- Future-proof: Extensible architecture for new features

Architecture:
- GuildPermissionRank: Defines permission ranks (Junior Mod, Moderator, etc.)
- GuildPermissionAssignment: Maps Discord roles to permission ranks
- GuildCommandPermission: Sets command-specific permission requirements

Note: "Rank" (0-100) is for permission hierarchy, "Level" is for XP/progression.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseCoordinator

# Removed: PermissionLevel enum - no longer needed
# The new system uses dynamic numeric ranks (0-100) with no hardcoded names
from tux.database.models.models import (
    GuildCommandPermission,
    GuildPermissionAssignment,
    GuildPermissionRank,
)

if TYPE_CHECKING:
    from tux.core.bot import Tux


class PermissionSystem:
    """
    Main permission system service that orchestrates all permission checking.

    This class provides:
    - Permission rank validation (0-100 hierarchy)
    - Role-based access control
    - Command-specific permissions
    - Caching for performance
    - Self-hosting configuration support

    Note: Ranks are for permissions, Levels are for XP/progression.
    """

    def __init__(self, bot: Tux, db: DatabaseCoordinator):
        self.bot = bot
        self.db = db

        # Caches for performance
        self._rank_cache: dict[int, dict[int, GuildPermissionRank]] = {}
        self._assignment_cache: dict[int, dict[int, GuildPermissionAssignment]] = {}
        self._command_cache: dict[int, dict[str, GuildCommandPermission]] = {}

        # Default permission ranks (can be overridden via config)
        self._default_ranks = {
            0: {"name": "Member", "description": "Basic server member"},
            1: {"name": "Trusted", "description": "Trusted server member"},
            2: {"name": "Junior Moderator", "description": "Can warn, timeout, jail"},
            3: {"name": "Moderator", "description": "Can kick, ban"},
            4: {"name": "Senior Moderator", "description": "Can unban, manage others"},
            5: {"name": "Administrator", "description": "Server administration"},
            6: {"name": "Head Administrator", "description": "Full server control"},
            7: {"name": "Server Owner", "description": "Complete access"},
        }

    async def initialize_guild(self, guild_id: int) -> None:
        """
        Initialize default permission ranks for a guild.

        This creates the standard permission hierarchy that servers can customize.
        """
        # Check if already initialized
        existing_ranks = await self.db.guild_permissions.get_permission_ranks_by_guild(guild_id)
        if existing_ranks:
            logger.info(f"Guild {guild_id} already has permission ranks initialized")
            return

        # Create default permission ranks
        for rank, data in self._default_ranks.items():
            await self.db.guild_permissions.create_permission_rank(
                guild_id=guild_id,
                rank=rank,
                name=data["name"],
                description=data["description"],
            )

        logger.info(f"Initialized default permission ranks for guild {guild_id}")

    # Removed: check_permission() method
    # This was redundant with the @requires_command_permission() decorator
    # Use the decorator in tux.core.decorators for all command permission checks

    async def get_user_permission_rank(self, ctx: commands.Context[Tux]) -> int:
        """
        Get the highest permission rank a user has in the current guild.

        Args:
            ctx: Command context

        Returns:
            Highest permission rank (0-100), 0 if none
        """
        if not ctx.guild:
            return 0

        # Get user's roles
        user_roles = []
        if isinstance(ctx.author, discord.Member):
            user_roles = [role.id for role in ctx.author.roles]

        # Get permission assignments for this guild
        return await self.db.permission_assignments.get_user_permission_rank(ctx.guild.id, ctx.author.id, user_roles)

    async def assign_permission_rank(
        self,
        guild_id: int,
        rank: int,
        role_id: int,
        assigned_by: int,
    ) -> GuildPermissionAssignment:
        """
        Assign a permission rank to a Discord role.

        Args:
            guild_id: Guild ID
            rank: Permission rank to assign (0-100)
            role_id: Discord role ID
            assigned_by: User ID who made the assignment

        Returns:
            Created assignment record
        """
        # Verify rank exists
        rank_info = await self.db.guild_permissions.get_permission_rank(guild_id, rank)
        if not rank_info or rank_info.id is None:
            error_msg = f"Permission rank {rank} does not exist for guild {guild_id}"
            raise ValueError(error_msg)

        # Create assignment
        assignment = await self.db.permission_assignments.assign_permission_rank(
            guild_id=guild_id,
            permission_rank_id=rank_info.id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

        # Clear cache for this guild
        self._clear_guild_cache(guild_id)

        logger.info(f"Assigned rank {rank} to role {role_id} in guild {guild_id}")
        return assignment

    async def create_custom_permission_rank(
        self,
        guild_id: int,
        rank: int,
        name: str,
        description: str | None = None,
        color: int | None = None,
    ) -> GuildPermissionRank:
        """
        Create a custom permission rank for a guild.

        Args:
            guild_id: Guild ID
            rank: Permission rank number (0-100)
            name: Display name for the rank
            description: Optional description
            color: Optional Discord color value

        Returns:
            Created permission rank
        """
        if rank < 0 or rank > 100:
            error_msg = "Permission rank must be between 0 and 100"
            raise ValueError(error_msg)

        permission_rank = await self.db.guild_permissions.create_permission_rank(
            guild_id=guild_id,
            rank=rank,
            name=name,
            description=description,
            color=color,
        )

        # Clear cache
        self._clear_guild_cache(guild_id)

        logger.info(f"Created custom permission rank {rank} ({name}) for guild {guild_id}")
        return permission_rank

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_rank: int,
        category: str | None = None,
    ) -> GuildCommandPermission:
        """
        Set the permission rank required for a specific command.

        Args:
            guild_id: Guild ID
            command_name: Command name
            required_rank: Required permission rank (0-100)
            category: Optional category for organization

        Returns:
            Command permission record
        """
        command_perm = await self.db.command_permissions.set_command_permission(
            guild_id=guild_id,
            command_name=command_name,
            required_rank=required_rank,
            category=category,
        )

        # Clear command cache for this guild
        if guild_id in self._command_cache:
            self._command_cache[guild_id].pop(command_name, None)

        logger.info(f"Set command {command_name} to require rank {required_rank} in guild {guild_id}")
        return command_perm

    async def get_command_permission(self, guild_id: int, command_name: str) -> GuildCommandPermission | None:
        """Get command-specific permission requirements."""
        return await self.db.command_permissions.get_command_permission(guild_id, command_name)

    async def get_guild_permission_ranks(self, guild_id: int) -> list[GuildPermissionRank]:
        """Get all permission ranks for a guild."""
        return await self.db.guild_permissions.get_permission_ranks_by_guild(guild_id)

    async def get_guild_assignments(self, guild_id: int) -> list[GuildPermissionAssignment]:
        """Get all permission assignments for a guild."""
        return await self.db.permission_assignments.get_assignments_by_guild(guild_id)

    async def get_guild_command_permissions(self, guild_id: int) -> list[GuildCommandPermission]:
        """Get all command permissions for a guild."""
        return await self.db.command_permissions.get_all_command_permissions(guild_id)

    def _clear_guild_cache(self, guild_id: int) -> None:
        """Clear all caches for a specific guild."""
        self._rank_cache.pop(guild_id, None)
        self._assignment_cache.pop(guild_id, None)
        self._command_cache.pop(guild_id, None)

    # Configuration file support for self-hosting
    async def load_from_config(self, guild_id: int, config: dict[str, Any]) -> None:
        """
        Load permission configuration from a config file.

        This allows self-hosters to define their permission structure
        via configuration files instead of using commands.
        """
        # Load permission ranks
        if "permission_ranks" in config:
            for rank_config in config["permission_ranks"]:
                await self.create_custom_permission_rank(
                    guild_id=guild_id,
                    rank=rank_config["rank"],
                    name=rank_config["name"],
                    description=rank_config.get("description"),
                    color=rank_config.get("color"),
                )

        # Load role assignments
        if "role_assignments" in config:
            for assignment in config["role_assignments"]:
                rank_info = await self.db.guild_permissions.get_permission_rank(guild_id, assignment["rank"])
                if rank_info:
                    await self.assign_permission_rank(
                        guild_id=guild_id,
                        rank=assignment["rank"],
                        role_id=assignment["role_id"],
                        assigned_by=self.bot.user.id if self.bot.user else 0,  # System assignment
                    )

        # Load command permissions
        if "command_permissions" in config:
            for cmd_perm in config["command_permissions"]:
                await self.set_command_permission(
                    guild_id=guild_id,
                    command_name=cmd_perm["command"],
                    required_rank=cmd_perm["rank"],
                    category=cmd_perm.get("category"),
                )

        logger.info(f"Loaded permission configuration for guild {guild_id} from config file")


# Global instance
_permission_system: PermissionSystem | None = None


def get_permission_system() -> PermissionSystem:
    """Get the global permission system instance."""
    if _permission_system is None:
        error_msg = "Permission system not initialized. Call init_permission_system() first."
        raise RuntimeError(error_msg)
    return _permission_system


def init_permission_system(bot: Tux, db: DatabaseCoordinator) -> PermissionSystem:
    """Initialize the global permission system."""
    # Use a more explicit approach to avoid global statement warning
    current_module = sys.modules[__name__]
    current_module._permission_system = PermissionSystem(bot, db)  # type: ignore[attr-defined]
    return current_module._permission_system
