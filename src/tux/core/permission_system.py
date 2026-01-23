"""Dynamic permission system for guild-specific permission hierarchies.

This module provides a database-driven permission system allowing guilds to customize
their permission ranks and role assignments. Supports dynamic permission ranks (0-10
hierarchy), role-based access control, command-specific permission overrides, performance
caching, and configuration file support for self-hosters. Note: "Rank" refers to
permission hierarchy (0-10), "Level" refers to XP/progression.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TypedDict

import discord
from discord.ext import commands
from loguru import logger
from sqlmodel import select

from tux.database.controllers import DatabaseCoordinator
from tux.database.models.models import (
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
)
from tux.shared.cache import TTLCache

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = [
    # Constants
    "DEFAULT_RANKS",
    "RESTRICTED_COMMANDS",
    # Classes
    "RankDefinition",
    "PermissionSystem",
    # Functions
    "get_permission_system",
    "init_permission_system",
]

# Default permission ranks hierarchy (0-7)
# This is the authoritative source for default rank definitions
DEFAULT_RANKS: dict[int, dict[str, str]] = {
    0: {
        "name": "Member",
        "description": "Regular community member with standard access to server features and commands",
    },
    1: {
        "name": "Trusted",
        "description": "Trusted community member who has proven themselves reliable and helpful",
    },
    2: {
        "name": "Junior Moderator",
        "description": "Entry-level moderation role for those learning and gaining experience",
    },
    3: {
        "name": "Moderator",
        "description": "Experienced moderator responsible for maintaining order and community standards",
    },
    4: {
        "name": "Senior Moderator",
        "description": "Senior moderator with additional oversight responsibilities and leadership duties",
    },
    5: {
        "name": "Administrator",
        "description": "Server administrator with broad management capabilities and configuration access",
    },
    6: {
        "name": "Head Administrator",
        "description": "Head administrator with comprehensive server oversight and decision-making authority",
    },
    7: {
        "name": "Server Owner",
        "description": "Server owner with ultimate authority and complete control over all aspects",
    },
}

# Commands that can NEVER be assigned to permission ranks (owner/sysadmin only)
# These commands are restricted at the bot level and must not be configurable
# via the permission system, config files, or UI.
RESTRICTED_COMMANDS: frozenset[str] = frozenset({"eval", "e", "jsk", "jishaku"})


class RankDefinition(TypedDict):
    """Type definition for permission rank configuration."""

    name: str
    description: str


class PermissionSystem:
    """
    Main permission system service orchestrating guild-specific permission checking.

    Manages the entire permission lifecycle including rank creation, role assignments,
    and command permissions. Permission ranks use numeric values (0-10) where higher
    numbers indicate greater permissions. This is separate from XP-based levels.

    Attributes
    ----------
    bot : Tux
        The bot instance for accessing guild/user data.
    db : DatabaseCoordinator
        Database coordinator for permission storage and retrieval.
    _default_ranks : dict[int, RankDefinition]
        Default permission rank hierarchy (0-7).
    """

    # Shared cache for command permissions with parent fallback (5 minute TTL)
    _command_permission_cache: TTLCache = TTLCache(ttl=300.0, max_size=2000)

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
        self._default_ranks = DEFAULT_RANKS

    # ---------- Guild Initialization ----------

    async def initialize_guild(self, guild_id: int) -> None:
        """
        Initialize default permission ranks for a guild.

        Creates the standard 8-rank hierarchy (0-7) for guilds that don't have them yet.
        This method is idempotent - it only creates ranks that are completely missing
        and never overwrites user customizations. Respects user customizations by
        creating missing default ranks, never updating existing ranks, and allowing
        guilds to fully customize their permission hierarchy after initial setup.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID to initialize.
        """
        logger.debug(f"PermissionSystem.initialize_guild called for guild {guild_id}")

        # Get existing ranks for this guild
        logger.trace(f"Checking existing ranks for guild {guild_id}")
        try:
            existing_ranks = (
                await self.db.permission_ranks.get_permission_ranks_by_guild(guild_id)
            )
            existing_rank_numbers = {r.rank for r in existing_ranks}
            logger.trace(
                f"Found {len(existing_ranks)} existing ranks for guild {guild_id}",
            )
        except Exception as e:
            logger.error(
                f"Error checking existing ranks for guild {guild_id}: {e}",
                exc_info=True,
            )
            raise

        # Only create ranks that don't exist at all
        # This preserves user customizations of existing ranks
        ranks_to_create: list[tuple[int, dict[str, str]]] = []
        for rank, default_data in DEFAULT_RANKS.items():
            if rank not in existing_rank_numbers:
                ranks_to_create.append((rank, default_data))
                logger.trace(f"Will create missing rank {rank}: {default_data['name']}")

        if not ranks_to_create:
            logger.info(
                f"All default ranks already exist for guild {guild_id} (customizations preserved)",
            )
            return

        # Create missing ranks in bulk for better performance
        logger.info(
            f"Creating {len(ranks_to_create)} missing default ranks for guild {guild_id}",
        )

        # Prepare bulk data
        bulk_data = [
            {
                "guild_id": guild_id,
                "rank": rank,
                "name": default_data["name"],
                "description": default_data["description"],
            }
            for rank, default_data in ranks_to_create
        ]

        try:
            await self.db.permission_ranks.bulk_create_permission_ranks(bulk_data)
            logger.debug(
                f"Successfully bulk created {len(ranks_to_create)} ranks for guild {guild_id}",
            )
        except Exception as e:
            logger.error(
                f"Error bulk creating ranks for guild {guild_id}: {e}",
                exc_info=True,
            )
            raise

        logger.success(
            f"Successfully initialized missing default ranks for guild {guild_id}",
        )

        logger.info(f"Initialized default permission ranks for guild {guild_id}")

    # ---------- Permission Checking ----------

    async def get_user_permission_rank(self, ctx: commands.Context[Tux]) -> int:
        """
        Get the highest permission rank a user has in the current guild.

        Checks all of the user's roles and returns the highest permission rank
        assigned to any of them. Returns 0 if the user has no permission ranks.
        Used internally by permission decorators to check if a user has sufficient
        permissions to run a command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context containing guild and user information.

        Returns
        -------
        int
            The highest permission rank (0-10) the user has, or 0 if none.
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
            The permission rank to assign (0-10).
        role_id : int
            The Discord role ID to assign the rank to.

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
        removed = await self.db.permission_assignments.remove_role_assignment(
            guild_id,
            role_id,
        )

        if removed:
            logger.info(
                f"Removed permission assignment for role {role_id} in guild {guild_id}",
            )

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
        names and descriptions. Rank numbers must be between 0-10.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        rank : int
            The permission rank number (0-10).
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
            If rank is not between 0 and 10.
        """
        # Validate rank range
        if rank < 0 or rank > 10:
            error_msg = "Permission rank must be between 0 and 10"
            raise ValueError(error_msg)

        # Create custom rank
        permission_rank = await self.db.permission_ranks.create_permission_rank(
            guild_id=guild_id,
            rank=rank,
            name=name,
            description=description,
        )

        logger.info(
            f"Created custom permission rank {rank} ({name}) for guild {guild_id}",
        )
        return permission_rank

    # ---------- Command Permission Management ----------

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_rank: int,
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
            The minimum permission rank required (0-10).

        Returns
        -------
        PermissionCommand
            The created or updated command permission record.

        Raises
        ------
        ValueError
            If required_rank is not between 0 and 10, or if command_name is restricted.
        """
        # Block restricted commands from being assigned to ranks
        if command_name.lower() in RESTRICTED_COMMANDS:
            error_msg = (
                f"Cannot assign permission rank to '{command_name}'. "
                f"This command is restricted to bot owners and sysadmins only."
            )
            logger.warning(
                f"Attempted to assign rank to restricted command '{command_name}' in guild {guild_id}",
            )
            raise ValueError(error_msg)

        # Validate rank range
        if required_rank < 0 or required_rank > 10:
            error_msg = f"Required rank must be between 0 and 10, got {required_rank}"
            raise ValueError(error_msg)

        # Set command permission in database (this will invalidate cache)
        command_perm = await self.db.command_permissions.set_command_permission(
            guild_id=guild_id,
            command_name=command_name,
            required_rank=required_rank,
        )

        # Invalidate cache for this command and potential parent commands
        cache_key = f"command_permission_fallback:{guild_id}:{command_name}"
        self._command_permission_cache.invalidate(cache_key)
        # Also invalidate parent command caches
        parts = command_name.split()
        for i in range(len(parts) - 1, 0, -1):
            parent_name = " ".join(parts[:i])
            parent_cache_key = f"command_permission_fallback:{guild_id}:{parent_name}"
            self._command_permission_cache.invalidate(parent_cache_key)
        logger.trace(
            f"Invalidated command permission fallback cache for {command_name} (guild {guild_id})",
        )

        logger.info(
            f"Set command {command_name} to require rank {required_rank} in guild {guild_id}",
        )
        return command_perm

    # ---------- Query Methods ----------

    async def get_command_permission(
        self,
        guild_id: int,
        command_name: str,
    ) -> PermissionCommand | None:
        """
        Get command-specific permission requirements for a guild.

        Checks the command itself first, then falls back to parent commands
        if the subcommand is not configured. For example, if "config ranks init"
        is not configured, it will check "config ranks", then "config".

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        command_name : str
            The command name to look up (e.g., "config ranks init").

        Returns
        -------
        PermissionCommand | None
            The command permission record, or None if no override exists.
        """
        # Check cache first
        cache_key = f"command_permission_fallback:{guild_id}:{command_name}"
        cached = self._command_permission_cache.get(cache_key)
        if cached is not None:
            logger.trace(
                f"Cache hit for command permission with fallback {command_name} (guild {guild_id})",
            )
            return cached

        # For single-word commands (no parents), use direct query for efficiency
        parts = command_name.split()
        if len(parts) == 1:
            # No parents to check, just query the command directly (uses cache)
            result = await self.db.command_permissions.get_command_permission(
                guild_id,
                command_name,
            )
            self._command_permission_cache.set(cache_key, result)
            return result

        # For multi-word commands, build list of all possible command names to check
        # e.g., "config ranks init" -> ["config ranks init", "config ranks", "config"]
        command_names_to_check = [
            command_name,
            *(" ".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)),
        ]

        # Batch query all possible command names at once
        # This is much faster than sequential queries
        async with self.db.command_permissions.db.session() as session:
            stmt = (
                select(PermissionCommand)
                .where(PermissionCommand.guild_id == guild_id)
                .where(
                    PermissionCommand.command_name.in_(command_names_to_check),  # type: ignore[attr-defined]
                )
            )
            result = await session.execute(stmt)
            found_permissions = list(result.scalars().all())

            # Expunge instances for use outside session
            for perm in found_permissions:
                session.expunge(perm)

        # Return the first match in order of specificity (command itself, then parents)
        # This ensures subcommand overrides take precedence
        result = None
        for name in command_names_to_check:
            for perm in found_permissions:
                if perm.command_name == name:
                    # Only log at trace level - this is expected behavior when subcommands
                    # inherit parent permissions, and happens frequently during help system
                    # permission checks for dropdown filtering
                    if name != command_name:
                        logger.trace(
                            f"Using parent command permission '{name}' for '{command_name}'",
                        )
                    result = perm
                    break
            if result:
                break

        # Cache the result (even if None)
        self._command_permission_cache.set(cache_key, result)
        logger.trace(
            f"Cached command permission with fallback for {command_name} (guild {guild_id})",
        )
        return result

    async def batch_get_command_permissions(
        self,
        guild_id: int,
        command_names: list[str],
    ) -> dict[str, PermissionCommand | None]:
        """
        Batch get command permissions for multiple commands at once.

        This is much more efficient than calling get_command_permission multiple
        times, as it batches all database queries. Used by the help system to
        check permissions for multiple subcommands simultaneously.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        command_names : list[str]
            List of command names to check (e.g., ["cases view", "cases search", "cases modify"]).

        Returns
        -------
        dict[str, PermissionCommand | None]
            Dictionary mapping command names to their permission records.
            Commands without permissions will have None values.
        """
        if not command_names:
            return {}

        # Build set of all command names to check (including parents)
        all_names_to_check: set[str] = set()
        command_to_parents: dict[str, list[str]] = {}

        for command_name in command_names:
            parts = command_name.split()
            command_names_to_check = [command_name]

            # Add all parent command names (most specific to least)
            for i in range(len(parts) - 1, 0, -1):
                parent_name = " ".join(parts[:i])
                command_names_to_check.append(parent_name)

            all_names_to_check.update(command_names_to_check)
            command_to_parents[command_name] = command_names_to_check

        # Batch query all command permissions at once
        async with self.db.command_permissions.db.session() as session:
            stmt = (
                select(PermissionCommand)
                .where(PermissionCommand.guild_id == guild_id)
                .where(
                    PermissionCommand.command_name.in_(all_names_to_check),  # type: ignore[attr-defined]
                )
            )
            result = await session.execute(stmt)
            found_permissions = list(result.scalars().all())

            # Expunge instances for use outside session
            for perm in found_permissions:
                session.expunge(perm)

        # Create lookup dict for fast access
        perm_lookup: dict[str, PermissionCommand] = {
            perm.command_name: perm for perm in found_permissions
        }

        # Build result dict, checking each command and its parents
        # Check command itself, then parents in order of specificity
        result_dict: dict[str, PermissionCommand | None] = {
            command_name: next(
                (
                    perm_lookup[name]
                    for name in command_to_parents[command_name]
                    if name in perm_lookup
                ),
                None,  # No permission found for this command or its parents
            )
            for command_name in command_names
        }

        return result_dict

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

    async def get_guild_command_permissions(
        self,
        guild_id: int,
    ) -> list[PermissionCommand]:
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

        Allows self-hosters to define their permission structure via configuration
        files instead of using commands. The config can include custom ranks, role
        assignments, and command permissions.

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
        ...     "permission_ranks": [
        ...         {"rank": 10, "name": "Elite Mod", "description": "Elite moderators"}
        ...     ],
        ...     "role_assignments": [{"rank": 10, "role_id": 123456789}],
        ...     "command_permissions": [{"command": "ban", "rank": 3}],
        ... }
        >>> await system.load_from_config(guild_id, config)
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
            all_ranks = {
                r.rank: r for r in await self.get_guild_permission_ranks(guild_id)
            }

            for assignment in config["role_assignments"]:
                if all_ranks.get(assignment["rank"]):
                    await self.assign_permission_rank(
                        guild_id=guild_id,
                        rank=assignment["rank"],
                        role_id=assignment["role_id"],
                    )
                else:
                    logger.warning(
                        f"Skipping role assignment: rank {assignment['rank']} not found for guild {guild_id}",
                    )

        # Load command permission overrides
        if "command_permissions" in config:
            for cmd_perm in config["command_permissions"]:
                command_name = cmd_perm["command"]
                # Skip restricted commands (they cannot be assigned to ranks)
                if command_name.lower() in RESTRICTED_COMMANDS:
                    logger.warning(
                        f"Skipping restricted command '{command_name}' in config for guild {guild_id}. "
                        "Restricted commands can only be used by bot owners and sysadmins.",
                    )
                    continue

                await self.set_command_permission(
                    guild_id=guild_id,
                    command_name=command_name,
                    required_rank=cmd_perm["rank"],
                )

        logger.info(
            f"Loaded permission configuration for guild {guild_id} from config file",
        )


# ---------- Global Instance Management ----------

_permission_system: PermissionSystem | None = None


def get_permission_system() -> PermissionSystem:
    """
    Get the global permission system instance.

    Call init_permission_system() during bot startup before using this.

    Returns
    -------
    PermissionSystem
        The global permission system instance.

    Raises
    ------
    RuntimeError
        If the permission system hasn't been initialized yet.
    """
    if _permission_system is None:
        error_msg = (
            "Permission system not initialized. Call init_permission_system() first."
        )
        raise RuntimeError(error_msg)
    return _permission_system


def init_permission_system(bot: Tux, db: DatabaseCoordinator) -> PermissionSystem:
    """
    Initialize the global permission system instance.

    Should be called once during bot startup, after database initialization.
    Uses module-level attribute assignment to avoid global statement warning.

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
    """
    # Set module-level variable without using global statement
    current_module = sys.modules[__name__]
    current_module._permission_system = PermissionSystem(bot, db)  # type: ignore[attr-defined]
    return current_module._permission_system
