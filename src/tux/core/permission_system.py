"""
Dynamic Permission System Service

This service provides a comprehensive, database-driven permission system that allows
servers to customize their permission levels and role assignments. It's designed to be:

- Flexible: Each server can define their own permission hierarchy
- Scalable: Supports thousands of servers with different configurations
- Self-hosting friendly: Works with configuration files or commands
- Developer-friendly: Clean API for easy integration
- Future-proof: Extensible architecture for new features

Architecture:
- GuildPermissionLevel: Defines permission levels (Junior Mod, Moderator, etc.)
- GuildPermissionAssignment: Maps Discord roles to permission levels
- GuildCommandPermission: Sets command-specific permission requirements
- GuildBlacklist: Blocks users/roles/channels from using commands
- GuildWhitelist: Allows specific access to premium features
"""

from __future__ import annotations

import sys
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseCoordinator


class PermissionLevel(Enum):
    """Standard permission levels with default names."""

    MEMBER = 0
    TRUSTED = 1
    JUNIOR_MODERATOR = 2
    MODERATOR = 3
    SENIOR_MODERATOR = 4
    ADMINISTRATOR = 5
    HEAD_ADMINISTRATOR = 6
    SERVER_OWNER = 7
    BOT_OWNER = 8

    @property
    def default_name(self) -> str:
        """Get the default display name for this permission level."""
        names = {
            0: "Member",
            1: "Trusted",
            2: "Junior Moderator",
            3: "Moderator",
            4: "Senior Moderator",
            5: "Administrator",
            6: "Head Administrator",
            7: "Server Owner",
            8: "Bot Owner",
        }
        return names[self.value]

    @property
    def is_special(self) -> bool:
        """Check if this is a special system-level permission."""
        return self == PermissionLevel.BOT_OWNER


from tux.database.models.models import (
    GuildBlacklist,
    GuildCommandPermission,
    GuildPermissionAssignment,
    GuildPermissionLevel,
    GuildWhitelist,
)

if TYPE_CHECKING:
    from tux.core.bot import Tux


class PermissionSystem:
    """
    Main permission system service that orchestrates all permission checking.

    This class provides:
    - Permission level validation
    - Role-based access control
    - Command-specific permissions
    - Blacklist/whitelist management
    - Caching for performance
    - Self-hosting configuration support
    """

    def __init__(self, bot: Tux, db: DatabaseCoordinator):
        self.bot = bot
        self.db = db

        # Caches for performance
        self._level_cache: dict[int, dict[int, GuildPermissionLevel]] = {}
        self._assignment_cache: dict[int, dict[int, GuildPermissionAssignment]] = {}
        self._command_cache: dict[int, dict[str, GuildCommandPermission]] = {}
        self._blacklist_cache: dict[int, list[GuildBlacklist]] = {}
        self._whitelist_cache: dict[int, dict[str, list[GuildWhitelist]]] = {}

        # Default permission levels (can be overridden via config)
        self._default_levels = {
            0: {"name": "Member", "description": "Basic server member"},
            1: {"name": "Trusted", "description": "Trusted server member"},
            2: {"name": "Junior Moderator", "description": "Entry-level moderation"},
            3: {"name": "Moderator", "description": "Can kick, ban, timeout"},
            4: {"name": "Senior Moderator", "description": "Can unban, manage others"},
            5: {"name": "Administrator", "description": "Server administration"},
            6: {"name": "Head Administrator", "description": "Full server control"},
            7: {"name": "Server Owner", "description": "Complete access"},
        }

    async def initialize_guild(self, guild_id: int) -> None:
        """
        Initialize default permission levels for a guild.

        This creates the standard permission hierarchy that servers can customize.
        """
        # Check if already initialized
        existing_levels = await self.db.guild_permissions.get_permission_levels_by_guild(guild_id)
        if existing_levels:
            logger.info(f"Guild {guild_id} already has permission levels initialized")
            return

        # Create default permission levels
        for level, data in self._default_levels.items():
            await self.db.guild_permissions.create_permission_level(
                guild_id=guild_id,
                level=level,
                name=data["name"],
                description=data["description"],
            )

        logger.info(f"Initialized default permission levels for guild {guild_id}")

    async def check_permission(
        self,
        ctx: commands.Context[Tux],
        required_level: int,
        command_name: str | None = None,
    ) -> bool:
        """
        Check if a user has the required permission level.

        Args:
            ctx: Command context
            required_level: Required permission level (0-100)
            command_name: Specific command to check (optional)

        Returns:
            True if user has permission, False otherwise
        """
        # Owner bypass
        if await self.bot.is_owner(ctx.author):
            return True

        # Guild owner bypass
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True

        # Check blacklist
        if await self.is_blacklisted(ctx):
            return False

        # Get user's permission level
        user_level = await self.get_user_permission_level(ctx)

        # Check if user meets required level
        if user_level < required_level:
            return False

        # Check command-specific permissions if specified
        if command_name and ctx.guild:
            command_perm = await self.get_command_permission(ctx.guild.id, command_name)
            if command_perm and command_perm.required_level > user_level:
                return False

        return True

    async def require_semantic_permission(
        self,
        ctx_or_interaction: commands.Context[Tux] | discord.Interaction[Any],
        semantic_name: str,
        default_level: PermissionLevel,
        command_name: str | None = None,
    ) -> None:
        """
        Require a semantic permission level that can be customized per guild.

        This method allows guilds to customize what level their semantic roles require,
        while providing sensible defaults for guilds that haven't configured them.

        Args:
            ctx_or_interaction: Either a command context or interaction
            semantic_name: The semantic name (e.g., "moderator", "admin")
            default_level: Default PermissionLevel if not configured by guild
            command_name: Specific command to check (optional)

        Raises:
            commands.MissingPermissions: For prefix commands
            app_commands.MissingPermissions: For slash commands
        """
        # Determine if this is a context or interaction
        if isinstance(ctx_or_interaction, commands.Context):
            ctx = ctx_or_interaction
            is_slash = False
            guild_id = ctx.guild.id if ctx.guild else None
        else:  # discord.Interaction
            # Create proper context from interaction using Discord.py's built-in method
            ctx = await commands.Context.from_interaction(ctx_or_interaction)  # type: ignore[misc]
            is_slash = True
            guild_id = ctx_or_interaction.guild.id if ctx_or_interaction.guild else None

        if not guild_id:
            error_msg = "Cannot check permissions outside of a guild"
            raise ValueError(error_msg)

        # Get the actual level this semantic role requires for this guild
        actual_level = await self._get_semantic_level_for_guild(guild_id, semantic_name, default_level)

        # Check permission using the resolved level
        has_permission = await self.check_permission(ctx, actual_level.value, command_name)  # type: ignore[arg-type]

        if not has_permission:
            if is_slash:
                # For slash commands
                raise app_commands.MissingPermissions(
                    missing_permissions=[f"permission_level_{actual_level.value}"],
                )
            # For prefix commands
            raise commands.MissingPermissions(missing_permissions=[f"permission_level_{actual_level.value}"])

    async def _get_semantic_level_for_guild(
        self,
        guild_id: int,
        semantic_name: str,
        default_level: PermissionLevel,
    ) -> PermissionLevel:
        """
        Get the actual permission level that a semantic role maps to for a specific guild.

        This allows guilds to customize what level their semantic roles require.
        For example, a guild might want "moderator" to require level 5 instead of the default level 3.

        Args:
            guild_id: The guild ID
            semantic_name: The semantic name (e.g., "moderator")
            default_level: Default level if not configured

        Returns:
            The actual PermissionLevel to use for this semantic role in this guild
        """
        # For now, we'll use the default levels
        # In the future, this could check a guild configuration table
        # that allows customizing semantic role mappings

        # TODO: Add guild-specific semantic role mappings
        # This would allow guilds to configure:
        # - "moderator" requires level 5 (instead of default 3)
        # - "admin" requires level 7 (instead of default 5)
        # etc.

        return default_level

    async def require_permission(
        self,
        ctx_or_interaction: commands.Context[Tux] | discord.Interaction[Any],
        required_level: PermissionLevel,
        command_name: str | None = None,
    ) -> None:
        """
        Require a specific permission level, raising an exception if not met.

        This method is used by the unified decorator and will raise appropriate
        Discord.py exceptions if the user doesn't have the required permissions.

        Args:
            ctx_or_interaction: Either a command context or interaction
            required_level: Required permission level
            command_name: Specific command to check (optional)

        Raises:
            commands.MissingPermissions: For prefix commands
            app_commands.MissingPermissions: For slash commands
        """
        # Determine if this is a context or interaction
        if isinstance(ctx_or_interaction, commands.Context):
            ctx = ctx_or_interaction
            is_slash = False
        else:  # discord.Interaction
            # Create proper context from interaction using Discord.py's built-in method
            ctx = await commands.Context.from_interaction(ctx_or_interaction)  # type: ignore[misc]
            is_slash = True

        # Check permission
        has_permission = await self.check_permission(ctx, required_level.value, command_name)  # type: ignore[misc]

        if not has_permission:
            if is_slash:
                # For slash commands
                raise app_commands.MissingPermissions(
                    missing_permissions=[f"permission_level_{required_level.value}"],
                )
            # For prefix commands
            raise commands.MissingPermissions(missing_permissions=[f"permission_level_{required_level.value}"])

    async def get_user_permission_level(self, ctx: commands.Context[Tux]) -> int:
        """
        Get the highest permission level a user has in the current guild.

        Args:
            ctx: Command context

        Returns:
            Highest permission level (0-100), 0 if none
        """
        if not ctx.guild:
            return 0

        # Get user's roles
        user_roles = []
        if isinstance(ctx.author, discord.Member):
            user_roles = [role.id for role in ctx.author.roles]

        # Get permission assignments for this guild
        return await self.db.permission_assignments.get_user_permission_level(ctx.guild.id, ctx.author.id, user_roles)

    async def assign_permission_level(
        self,
        guild_id: int,
        level: int,
        role_id: int,
        assigned_by: int,
    ) -> GuildPermissionAssignment:
        """
        Assign a permission level to a Discord role.

        Args:
            guild_id: Guild ID
            level: Permission level to assign
            role_id: Discord role ID
            assigned_by: User ID who made the assignment

        Returns:
            Created assignment record
        """
        # Verify level exists
        level_info = await self.db.guild_permissions.get_permission_level(guild_id, level)
        if not level_info or level_info.id is None:
            error_msg = f"Permission level {level} does not exist for guild {guild_id}"
            raise ValueError(error_msg)

        # Create assignment
        assignment = await self.db.permission_assignments.assign_permission_level(
            guild_id=guild_id,
            permission_level_id=level_info.id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

        # Clear cache for this guild
        self._clear_guild_cache(guild_id)

        logger.info(f"Assigned level {level} to role {role_id} in guild {guild_id}")
        return assignment

    async def create_custom_permission_level(
        self,
        guild_id: int,
        level: int,
        name: str,
        description: str | None = None,
        color: int | None = None,
    ) -> GuildPermissionLevel:
        """
        Create a custom permission level for a guild.

        Args:
            guild_id: Guild ID
            level: Permission level number (0-100)
            name: Display name for the level
            description: Optional description
            color: Optional Discord color value

        Returns:
            Created permission level
        """
        if level < 0 or level > 100:
            error_msg = "Permission level must be between 0 and 100"
            raise ValueError(error_msg)

        permission_level = await self.db.guild_permissions.create_permission_level(
            guild_id=guild_id,
            level=level,
            name=name,
            description=description,
            color=color,
        )

        # Clear cache
        self._clear_guild_cache(guild_id)

        logger.info(f"Created custom permission level {level} ({name}) for guild {guild_id}")
        return permission_level

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_level: int,
        category: str | None = None,
    ) -> GuildCommandPermission:
        """
        Set the permission level required for a specific command.

        Args:
            guild_id: Guild ID
            command_name: Command name
            required_level: Required permission level
            category: Optional category for organization

        Returns:
            Command permission record
        """
        command_perm = await self.db.command_permissions.set_command_permission(
            guild_id=guild_id,
            command_name=command_name,
            required_level=required_level,
            category=category,
        )

        # Clear command cache for this guild
        if guild_id in self._command_cache:
            self._command_cache[guild_id].pop(command_name, None)

        logger.info(f"Set command {command_name} to require level {required_level} in guild {guild_id}")
        return command_perm

    async def blacklist_user(
        self,
        guild_id: int,
        user_id: int,
        blacklisted_by: int,
        reason: str | None = None,
        expires_at: datetime | None = None,
    ) -> GuildBlacklist:
        """
        Blacklist a user from using commands in the guild.

        Args:
            guild_id: Guild ID
            user_id: User ID to blacklist
            blacklisted_by: User ID who created the blacklist
            reason: Optional reason for blacklisting
            expires_at: Optional expiration date

        Returns:
            Blacklist record
        """
        blacklist = await self.db.guild_blacklist.add_to_blacklist(
            guild_id=guild_id,
            target_type="user",
            target_id=user_id,
            blacklisted_by=blacklisted_by,
            reason=reason,
            expires_at=expires_at,
        )

        # Clear blacklist cache
        self._blacklist_cache.pop(guild_id, None)

        logger.info(f"Blacklisted user {user_id} in guild {guild_id}")
        return blacklist

    async def whitelist_user(
        self,
        guild_id: int,
        user_id: int,
        feature: str,
        whitelisted_by: int,
    ) -> GuildWhitelist:
        """
        Whitelist a user for a specific feature.

        Args:
            guild_id: Guild ID
            user_id: User ID to whitelist
            feature: Feature name (e.g., "premium", "admin")
            whitelisted_by: User ID who created the whitelist

        Returns:
            Whitelist record
        """
        whitelist = await self.db.guild_whitelist.add_to_whitelist(
            guild_id=guild_id,
            target_type="user",
            target_id=user_id,
            feature=feature,
            whitelisted_by=whitelisted_by,
        )

        # Clear whitelist cache
        if guild_id in self._whitelist_cache:
            self._whitelist_cache[guild_id].pop(feature, None)

        logger.info(f"Whitelisted user {user_id} for feature {feature} in guild {guild_id}")
        return whitelist

    async def is_blacklisted(self, ctx: commands.Context[Tux]) -> bool:
        """
        Check if a user is blacklisted from using commands.

        Args:
            ctx: Command context

        Returns:
            True if blacklisted, False otherwise
        """
        if not ctx.guild:
            return False

        # Check user blacklist
        user_blacklist = await self.db.guild_blacklist.is_blacklisted(ctx.guild.id, "user", ctx.author.id)
        if user_blacklist:
            return True

        # Check role blacklists
        if isinstance(ctx.author, discord.Member):
            for role in ctx.author.roles:
                role_blacklist = await self.db.guild_blacklist.is_blacklisted(ctx.guild.id, "role", role.id)
                if role_blacklist:
                    return True

        # Check channel blacklist
        if ctx.channel:
            channel_blacklist = await self.db.guild_blacklist.is_blacklisted(ctx.guild.id, "channel", ctx.channel.id)
            if channel_blacklist:
                return True

        return False

    async def is_whitelisted(self, ctx: commands.Context[Tux], feature: str) -> bool:
        """
        Check if a user is whitelisted for a specific feature.

        Args:
            ctx: Command context
            feature: Feature name to check

        Returns:
            True if whitelisted, False otherwise
        """
        if not ctx.guild:
            return False

        return await self.db.guild_whitelist.is_whitelisted(ctx.guild.id, "user", ctx.author.id, feature)

    async def get_command_permission(self, guild_id: int, command_name: str) -> GuildCommandPermission | None:
        """Get command-specific permission requirements."""
        return await self.db.command_permissions.get_command_permission(guild_id, command_name)

    async def get_guild_permission_levels(self, guild_id: int) -> list[GuildPermissionLevel]:
        """Get all permission levels for a guild."""
        return await self.db.guild_permissions.get_permission_levels_by_guild(guild_id)

    async def get_guild_assignments(self, guild_id: int) -> list[GuildPermissionAssignment]:
        """Get all permission assignments for a guild."""
        return await self.db.permission_assignments.get_assignments_by_guild(guild_id)

    async def get_guild_command_permissions(self, guild_id: int) -> list[GuildCommandPermission]:
        """Get all command permissions for a guild."""
        return await self.db.command_permissions.get_all_command_permissions(guild_id)

    def _clear_guild_cache(self, guild_id: int) -> None:
        """Clear all caches for a specific guild."""
        self._level_cache.pop(guild_id, None)
        self._assignment_cache.pop(guild_id, None)
        self._command_cache.pop(guild_id, None)
        self._blacklist_cache.pop(guild_id, None)
        self._whitelist_cache.pop(guild_id, None)

    # Configuration file support for self-hosting
    async def load_from_config(self, guild_id: int, config: dict[str, Any]) -> None:
        """
        Load permission configuration from a config file.

        This allows self-hosters to define their permission structure
        via configuration files instead of using commands.
        """
        # Load permission levels
        if "permission_levels" in config:
            for level_config in config["permission_levels"]:
                await self.create_custom_permission_level(
                    guild_id=guild_id,
                    level=level_config["level"],
                    name=level_config["name"],
                    description=level_config.get("description"),
                    color=level_config.get("color"),
                )

        # Load role assignments
        if "role_assignments" in config:
            for assignment in config["role_assignments"]:
                level_info = await self.db.guild_permissions.get_permission_level(guild_id, assignment["level"])
                if level_info:
                    await self.assign_permission_level(
                        guild_id=guild_id,
                        level=assignment["level"],
                        role_id=assignment["role_id"],
                        assigned_by=self.bot.user.id if self.bot.user else 0,  # System assignment
                    )

        # Load command permissions
        if "command_permissions" in config:
            for cmd_perm in config["command_permissions"]:
                await self.set_command_permission(
                    guild_id=guild_id,
                    command_name=cmd_perm["command"],
                    required_level=cmd_perm["level"],
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
