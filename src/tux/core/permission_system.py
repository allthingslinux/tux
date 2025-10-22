"""
Dynamic permission system for guild-specific permission hierarchies.

This module provides a database-driven permission system allowing guilds to customize
their permission ranks and role assignments. Key features:

- Dynamic permission ranks (0-100 hierarchy)
- Role-based access control
- Command-specific permission overrides
- Performance caching
- Configuration file support for self-hosters

Architecture:
    - PermissionRank: Defines permission ranks (e.g., Moderator, Admin)
    - PermissionAssignment: Maps Discord roles to permission ranks
    - PermissionCommand: Sets command-specific permission requirements

Note:
    "Rank" refers to permission hierarchy (0-100), "Level" refers to XP/progression.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TypedDict

import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseCoordinator
from tux.database.models.models import (
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
)

if TYPE_CHECKING:
    from tux.core.bot import Tux


class RankDefinition(TypedDict):
    """Type definition for permission rank configuration."""

    name: str
    description: str


class PermissionSystem:
    """
    Main permission system service orchestrating guild-specific permission checking.

    This class manages the entire permission lifecycle including rank creation,
    role assignments, and command permissions.

    Attributes
    ----------
    bot : Tux
        The bot instance for accessing guild/user data.
    db : DatabaseCoordinator
        Database coordinator for permission storage and retrieval.
    _default_ranks : dict[int, RankDefinition]
        Default permission rank hierarchy (0-7).

    Notes
    -----
    Permission ranks use numeric values (0-100) where higher numbers indicate
    greater permissions. This is separate from XP-based levels.
    """

    def __init__(self, bot: Tux, db: DatabaseCoordinator) -> None:
        """
        Initialize the permission system with bot and database connections.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        db : DatabaseCoordinator
            The database coordinator.
        """
        self.bot = bot
        self.db = db

        # Default permission rank hierarchy (0-7)
        # Guilds can customize these ranks or add their own
        self._default_ranks: dict[int, RankDefinition] = {
            0: {"name": "Member", "description": "Basic server member"},
            1: {"name": "Trusted", "description": "Trusted server member"},
            2: {"name": "Junior Moderator", "description": "Can warn, timeout, jail"},
            3: {"name": "Moderator", "description": "Can kick, ban"},
            4: {"name": "Senior Moderator", "description": "Can unban, manage others"},
            5: {"name": "Administrator", "description": "Server administration"},
            6: {"name": "Head Administrator", "description": "Full server control"},
            7: {"name": "Server Owner", "description": "Complete access"},
        }

    # ---------- Guild Initialization ----------

    async def initialize_guild(self, guild_id: int) -> None:
        """
        Initialize default permission ranks for a guild.

        Creates the standard 8-rank hierarchy (0-7) that guilds can customize.
        If ranks already exist, this method does nothing (idempotent).

        Parameters
        ----------
        guild_id : int
            The Discord guild ID to initialize.

        Notes
        -----
        This is typically called automatically when a guild is first added to
        the bot. The default ranks can be customized via commands or config files.
        """
        # Check if already initialized (idempotent check)
        existing_ranks = await self.db.permission_ranks.get_permission_ranks_by_guild(guild_id)
        if existing_ranks:
            logger.info(f"Guild {guild_id} already has permission ranks initialized")
            return

        # Create default permission ranks (0-7)
        for rank, data in self._default_ranks.items():
            await self.db.permission_ranks.create_permission_rank(
                guild_id=guild_id,
                rank=rank,
                name=data["name"],
                description=data["description"],
            )

        logger.info(f"Initialized default permission ranks for guild {guild_id}")

    # ---------- Permission Checking ----------

    async def get_user_permission_rank(self, ctx: commands.Context[Tux]) -> int:
        """
        Get the highest permission rank a user has in the current guild.

        Checks all of the user's roles and returns the highest permission rank
        assigned to any of them. Returns 0 if the user has no permission ranks.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context containing guild and user information.

        Returns
        -------
        int
            The highest permission rank (0-100) the user has, or 0 if none.

        Notes
        -----
        This method is used internally by permission decorators to check if
        a user has sufficient permissions to run a command.
        """
        # DM context has no permissions
        if not ctx.guild:
            return 0

        # Extract role IDs from user's Discord roles
        user_roles = []
        if isinstance(ctx.author, discord.Member):
            user_roles = [role.id for role in ctx.author.roles]

        # Query database for highest rank among user's roles
        return await self.db.permission_assignments.get_user_permission_rank(
            ctx.guild.id,
            ctx.author.id,
            user_roles,
        )

    # ---------- Role Assignment Management ----------

    async def assign_permission_rank(
        self,
        guild_id: int,
        rank: int,
        role_id: int,
        assigned_by: int,
    ) -> PermissionAssignment:
        """
        Assign a permission rank to a Discord role.

        Links a Discord role to a permission rank, granting all members with that
        role the specified permission level. Invalidates cache after assignment.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        rank : int
            The permission rank to assign (0-100).
        role_id : int
            The Discord role ID to assign the rank to.
        assigned_by : int
            The user ID who made this assignment (for auditing).

        Returns
        -------
        PermissionAssignment
            The created assignment record.

        Raises
        ------
        ValueError
            If the specified rank doesn't exist for the guild.
        """
        # Verify rank exists before creating assignment
        rank_info = await self.db.permission_ranks.get_permission_rank(guild_id, rank)
        if not rank_info or rank_info.id is None:
            error_msg = f"Permission rank {rank} does not exist for guild {guild_id}"
            raise ValueError(error_msg)

        # Create role-to-rank assignment
        assignment = await self.db.permission_assignments.assign_permission_rank(
            guild_id=guild_id,
            permission_rank_id=rank_info.id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

        logger.info(f"Assigned rank {rank} to role {role_id} in guild {guild_id}")
        return assignment

    async def remove_role_assignment(self, guild_id: int, role_id: int) -> bool:
        """
        Remove permission rank assignment from a Discord role.

        Unlinks a role from its permission rank. Members with this role will no
        longer have the associated permissions.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        role_id : int
            The Discord role ID to remove the assignment from.

        Returns
        -------
        bool
            True if an assignment was removed, False if no assignment existed.
        """
        removed = await self.db.permission_assignments.remove_role_assignment(guild_id, role_id)

        if removed:
            logger.info(f"Removed permission assignment for role {role_id} in guild {guild_id}")

        return removed

    # ---------- Custom Rank Management ----------

    async def create_custom_permission_rank(
        self,
        guild_id: int,
        rank: int,
        name: str,
        description: str | None = None,
    ) -> PermissionRank:
        """
        Create a custom permission rank for a guild.

        Guilds can create custom ranks or override default ranks with their own
        names and descriptions. Rank numbers must be between 0-100.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        rank : int
            The permission rank number (0-100).
        name : str
            Display name for the rank (e.g., "Super Moderator").
        description : str | None, optional
            Optional description of the rank's permissions.

        Returns
        -------
        PermissionRank
            The created permission rank record.

        Raises
        ------
        ValueError
            If rank is not between 0 and 100.
        """
        # Validate rank range
        if rank < 0 or rank > 100:
            error_msg = "Permission rank must be between 0 and 100"
            raise ValueError(error_msg)

        # Create custom rank
        permission_rank = await self.db.permission_ranks.create_permission_rank(
            guild_id=guild_id,
            rank=rank,
            name=name,
            description=description,
        )

        logger.info(f"Created custom permission rank {rank} ({name}) for guild {guild_id}")
        return permission_rank

    # ---------- Command Permission Management ----------

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_rank: int,
        category: str | None = None,
    ) -> PermissionCommand:
        """
        Set the permission rank required for a specific command.

        Overrides the default permission requirements for a command in a specific
        guild. This allows guilds to customize which ranks can use which commands.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        command_name : str
            The command name (without prefix).
        required_rank : int
            The minimum permission rank required (0-100).
        category : str | None, optional
            Optional category for organizing command permissions.

        Returns
        -------
        PermissionCommand
            The created or updated command permission record.

        Raises
        ------
        ValueError
            If required_rank is not between 0 and 100.
        """
        # Validate rank range
        if required_rank < 0 or required_rank > 100:
            error_msg = f"Required rank must be between 0 and 100, got {required_rank}"
            raise ValueError(error_msg)

        # Set command permission in database
        command_perm = await self.db.command_permissions.set_command_permission(
            guild_id=guild_id,
            command_name=command_name,
            required_rank=required_rank,
            category=category,
        )

        logger.info(f"Set command {command_name} to require rank {required_rank} in guild {guild_id}")
        return command_perm

    # ---------- Query Methods ----------

    async def get_command_permission(self, guild_id: int, command_name: str) -> PermissionCommand | None:
        """
        Get command-specific permission requirements for a guild.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        command_name : str
            The command name to look up.

        Returns
        -------
        PermissionCommand | None
            The command permission record, or None if no override exists.
        """
        return await self.db.command_permissions.get_command_permission(guild_id, command_name)

    async def get_guild_permission_ranks(self, guild_id: int) -> list[PermissionRank]:
        """
        Get all permission ranks defined for a guild.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        list[PermissionRank]
            List of all permission ranks for the guild.
        """
        return await self.db.permission_ranks.get_permission_ranks_by_guild(guild_id)

    async def get_guild_assignments(self, guild_id: int) -> list[PermissionAssignment]:
        """
        Get all role-to-rank assignments for a guild.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        list[PermissionAssignment]
            List of all role assignments for the guild.
        """
        return await self.db.permission_assignments.get_assignments_by_guild(guild_id)

    async def get_guild_command_permissions(self, guild_id: int) -> list[PermissionCommand]:
        """
        Get all command permission overrides for a guild.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        list[PermissionCommand]
            List of all command permission overrides for the guild.
        """
        return await self.db.command_permissions.get_all_command_permissions(guild_id)

    # ---------- Configuration File Support ----------

    async def load_from_config(self, guild_id: int, config: dict[str, Any]) -> None:
        """
        Load permission configuration from a configuration file.

        This allows self-hosters to define their permission structure via
        configuration files instead of using commands. The config can include
        custom ranks, role assignments, and command permissions.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID to configure.
        config : dict[str, Any]
            Configuration dictionary with optional keys:
            - permission_ranks: List of rank definitions
            - role_assignments: List of role-to-rank assignments
            - command_permissions: List of command permission overrides

        Examples
        --------
        >>> config = {
        ...     "permission_ranks": [{"rank": 10, "name": "Elite Mod", "description": "Elite moderators"}],
        ...     "role_assignments": [{"rank": 10, "role_id": 123456789}],
        ...     "command_permissions": [{"command": "ban", "rank": 3, "category": "moderation"}],
        ... }
        >>> await system.load_from_config(guild_id, config)

        Notes
        -----
        Role assignments are marked as system-assigned (assigned_by = bot user ID).
        """
        # Load custom permission ranks
        if "permission_ranks" in config:
            for rank_config in config["permission_ranks"]:
                await self.create_custom_permission_rank(
                    guild_id=guild_id,
                    rank=rank_config["rank"],
                    name=rank_config["name"],
                    description=rank_config.get("description"),
                )

        # Load role-to-rank assignments (batch load ranks to avoid N+1 queries)
        if "role_assignments" in config:
            # Batch load all ranks once to avoid N+1 queries
            all_ranks = {r.rank: r for r in await self.get_guild_permission_ranks(guild_id)}

            for assignment in config["role_assignments"]:
                if all_ranks.get(assignment["rank"]):
                    await self.assign_permission_rank(
                        guild_id=guild_id,
                        rank=assignment["rank"],
                        role_id=assignment["role_id"],
                        assigned_by=self.bot.user.id if self.bot.user else 0,  # System assignment
                    )
                else:
                    logger.warning(
                        f"Skipping role assignment: rank {assignment['rank']} not found for guild {guild_id}",
                    )

        # Load command permission overrides
        if "command_permissions" in config:
            for cmd_perm in config["command_permissions"]:
                await self.set_command_permission(
                    guild_id=guild_id,
                    command_name=cmd_perm["command"],
                    required_rank=cmd_perm["rank"],
                    category=cmd_perm.get("category"),
                )

        logger.info(f"Loaded permission configuration for guild {guild_id} from config file")


# ---------- Global Instance Management ----------

_permission_system: PermissionSystem | None = None


def get_permission_system() -> PermissionSystem:
    """
    Get the global permission system instance.

    Returns
    -------
    PermissionSystem
        The global permission system instance.

    Raises
    ------
    RuntimeError
        If the permission system hasn't been initialized yet.

    Notes
    -----
    Call `init_permission_system()` during bot startup before using this.
    """
    if _permission_system is None:
        error_msg = "Permission system not initialized. Call init_permission_system() first."
        raise RuntimeError(error_msg)
    return _permission_system


def init_permission_system(bot: Tux, db: DatabaseCoordinator) -> PermissionSystem:
    """
    Initialize the global permission system instance.

    This should be called once during bot startup, after database initialization.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    db : DatabaseCoordinator
        The database coordinator.

    Returns
    -------
    PermissionSystem
        The initialized permission system instance.

    Notes
    -----
    Uses module-level attribute assignment to avoid global statement warning.
    """
    # Set module-level variable without using global statement
    current_module = sys.modules[__name__]
    current_module._permission_system = PermissionSystem(bot, db)  # type: ignore[attr-defined]
    return current_module._permission_system
