"""
Dynamic permission system controllers.

Provides database operations for the flexible permission system that allows
servers to customize their permission levels and role assignments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import discord
from loguru import logger
from sqlmodel import select

from tux.cache import TTLCache
from tux.database.controllers.base import BaseController
from tux.database.models.models import (
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
)
from tux.services.sentry import capture_exception_safe

if TYPE_CHECKING:
    from tux.cache import AsyncCacheBackendProtocol
    from tux.database.service import DatabaseService

PERM_KEY_PREFIX = "perm:"
# Ranks and assignments: setup-once; invalidated on config change.
PERM_RANKS_TTL = 7200.0  # 2 hours
# User rank (derived from roles); invalidated when assignments change.
PERM_USER_RANK_TTL = 7200.0  # 2 hours


class PermissionRankController(BaseController[PermissionRank]):
    """Controller for managing guild permission ranks."""

    # Shared cache for permission ranks when no backend
    _ranks_cache: TTLCache = TTLCache(ttl=PERM_RANKS_TTL, max_size=1000)
    _guild_ranks_cache: TTLCache = TTLCache(ttl=PERM_RANKS_TTL, max_size=500)

    def __init__(
        self,
        db: DatabaseService | None = None,
        cache_backend: AsyncCacheBackendProtocol | None = None,
    ) -> None:
        """
        Initialize the guild permission rank controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        cache_backend : AsyncCacheBackendProtocol | None, optional
            Optional cache backend (Valkey/in-memory) for permission ranks.
        """
        super().__init__(PermissionRank, db)
        self._backend = cache_backend

    async def create_permission_rank(
        self,
        guild_id: int,
        rank: int,
        name: str,
        description: str | None = None,
    ) -> PermissionRank:
        """
        Create a new permission rank for a guild.

        Returns
        -------
        PermissionRank
            The newly created permission rank.
        """
        logger.debug(
            f"Creating permission rank: guild_id={guild_id}, rank={rank}, name={name}",
        )
        try:
            result = await self.create(
                guild_id=guild_id,
                rank=rank,
                name=name,
                description=description,
            )
            # Invalidate cache for this guild
            if self._backend is not None:
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}permission_ranks:{guild_id}",
                )
                if result.id is not None:
                    await self._backend.delete(
                        f"{PERM_KEY_PREFIX}permission_rank:{result.id}",
                    )
            else:
                self._guild_ranks_cache.invalidate(f"permission_ranks:{guild_id}")
                if result.id:
                    self._ranks_cache.invalidate(f"permission_rank:{result.id}")
            logger.trace(f"Invalidated permission rank cache for guild {guild_id}")
        except Exception as e:
            logger.error(
                f"Error creating permission rank {rank} for guild {guild_id}: {e}",
            )

            capture_exception_safe(
                e,
                extra_context={
                    "operation": "create_permission_rank",
                    "guild_id": str(guild_id),
                    "rank": str(rank),
                },
            )
            raise
        else:
            logger.debug(
                f"Successfully created permission rank {rank} for guild {guild_id}",
            )
            return result

    async def get_permission_ranks_by_guild(
        self,
        guild_id: int,
    ) -> list[PermissionRank]:
        """
        Get all permission ranks for a guild.

        Returns
        -------
        list[PermissionRank]
            List of permission ranks ordered by rank value.
        """
        backend_key = f"{PERM_KEY_PREFIX}permission_ranks:{guild_id}"
        if self._backend is not None:
            raw = await self._backend.get(backend_key)
            if raw is not None and isinstance(raw, list):
                logger.trace(f"Cache hit for permission ranks (guild {guild_id})")
                items = cast(list[dict[str, Any]], raw)
                return [PermissionRank.model_validate(d) for d in items]
        else:
            cache_key = f"permission_ranks:{guild_id}"
            cached = self._guild_ranks_cache.get(cache_key)
            if cached is not None:
                logger.trace(f"Cache hit for permission ranks (guild {guild_id})")
                return cached

        result = await self.find_all(
            filters=PermissionRank.guild_id == guild_id,
            order_by=PermissionRank.rank,
        )
        if self._backend is not None:
            await self._backend.set(
                backend_key,
                [m.model_dump() for m in result],
                ttl_sec=PERM_RANKS_TTL,
            )
        else:
            self._guild_ranks_cache.set(f"permission_ranks:{guild_id}", result)
        logger.trace(f"Cached permission ranks for guild {guild_id}")
        return result

    async def get_permission_rank(
        self,
        guild_id: int,
        rank: int,
    ) -> PermissionRank | None:
        """
        Get a specific permission rank.

        Returns
        -------
        PermissionRank | None
            The permission rank if found, None otherwise.
        """
        return await self.find_one(
            filters=(PermissionRank.guild_id == guild_id)
            & (PermissionRank.rank == rank),
        )

    async def update_permission_rank(
        self,
        guild_id: int,
        rank: int,
        name: str | None = None,
        description: str | None = discord.utils.MISSING,
    ) -> PermissionRank | None:
        """
        Update a permission rank.

        Pass ``description=None`` to clear the description; omit the argument
        to leave it unchanged.

        Returns
        -------
        PermissionRank | None
            The updated permission rank, or None if not found.
        """
        # Find the record first
        record = await self.find_one(
            filters=(PermissionRank.guild_id == guild_id)
            & (PermissionRank.rank == rank),
        )
        if not record:
            return None

        # Update the record
        update_data: dict[str, str | None] = {}
        if name is not None:
            update_data["name"] = name
        if description is not discord.utils.MISSING:
            update_data["description"] = description  # None clears it
        # Note: updated_at is automatically managed by the database via TimestampMixin

        result = await self.update_by_id(record.id, **update_data)
        # Invalidate cache
        if self._backend is not None:
            await self._backend.delete(
                f"{PERM_KEY_PREFIX}permission_ranks:{guild_id}",
            )
            if record.id is not None:
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}permission_rank:{record.id}",
                )
        else:
            self._guild_ranks_cache.invalidate(f"permission_ranks:{guild_id}")
            if record.id:
                self._ranks_cache.invalidate(f"permission_rank:{record.id}")
        logger.trace(f"Invalidated permission rank cache for guild {guild_id}")
        return result

    async def bulk_create_permission_ranks(
        self,
        ranks_data: list[dict[str, Any]],
    ) -> list[PermissionRank]:
        """
        Bulk create multiple permission ranks in a single transaction.

        Parameters
        ----------
        ranks_data : list[dict[str, Any]]
            List of rank data dictionaries, each containing guild_id, rank, name, description

        Returns
        -------
        list[PermissionRank]
            List of created permission rank instances
        """
        logger.debug(f"Bulk creating {len(ranks_data)} permission ranks")
        try:
            async with self.db.session() as session:
                instances: list[PermissionRank] = []
                for data in ranks_data:
                    instance = self.model(**data)
                    session.add(instance)
                    instances.append(instance)

                await session.commit()

                # Refresh all instances to get auto-generated fields
                for instance in instances:
                    try:
                        await session.refresh(instance)
                    except Exception as e:
                        logger.warning(f"Refresh failed for {self.model.__name__}: {e}")

                # Expunge all instances
                for instance in instances:
                    session.expunge(instance)

                # Invalidate cache for all affected guilds
                affected_guild_ids = {instance.guild_id for instance in instances}
                if self._backend is not None:
                    for guild_id in affected_guild_ids:
                        await self._backend.delete(
                            f"{PERM_KEY_PREFIX}permission_ranks:{guild_id}",
                        )
                        logger.trace(
                            f"Invalidated permission ranks cache for guild {guild_id}",
                        )
                else:
                    for guild_id in affected_guild_ids:
                        self._guild_ranks_cache.invalidate(
                            f"permission_ranks:{guild_id}",
                        )
                        logger.trace(
                            f"Invalidated permission ranks cache for guild {guild_id}",
                        )

                logger.debug(
                    f"Successfully bulk created {len(instances)} permission ranks",
                )
                return instances

        except Exception as e:
            logger.error(f"Error bulk creating permission ranks: {e}")
            capture_exception_safe(
                e,
                extra_context={
                    "operation": "bulk_create_permission_ranks",
                    "count": str(len(ranks_data)),
                },
            )
            raise

    async def delete_permission_rank(self, guild_id: int, rank: int) -> bool:
        """
        Delete a permission rank.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        # Get the record first to invalidate cache
        record = await self.find_one(
            filters=(PermissionRank.guild_id == guild_id)
            & (PermissionRank.rank == rank),
        )
        deleted_count = await self.delete_where(
            filters=(PermissionRank.guild_id == guild_id)
            & (PermissionRank.rank == rank),
        )
        if deleted_count > 0:
            if self._backend is not None:
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}permission_ranks:{guild_id}",
                )
                if record is not None and record.id is not None:
                    await self._backend.delete(
                        f"{PERM_KEY_PREFIX}permission_rank:{record.id}",
                    )
            else:
                self._guild_ranks_cache.invalidate(f"permission_ranks:{guild_id}")
                if record and record.id:
                    self._ranks_cache.invalidate(f"permission_rank:{record.id}")
            logger.trace(f"Invalidated permission rank cache for guild {guild_id}")
        return deleted_count > 0


class PermissionAssignmentController(BaseController[PermissionAssignment]):
    """Controller for managing guild permission assignments."""

    # Shared cache when no backend
    _assignments_cache: TTLCache = TTLCache(ttl=PERM_RANKS_TTL, max_size=500)
    _user_rank_cache: TTLCache = TTLCache(ttl=PERM_USER_RANK_TTL, max_size=5000)

    def __init__(
        self,
        db: DatabaseService | None = None,
        cache_backend: AsyncCacheBackendProtocol | None = None,
    ) -> None:
        """Initialize the guild permission assignment controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        cache_backend : AsyncCacheBackendProtocol | None, optional
            Optional cache backend (Valkey/in-memory) for assignments and user rank.
        """
        super().__init__(PermissionAssignment, db)
        self._backend = cache_backend

    async def assign_permission_rank(
        self,
        guild_id: int,
        permission_rank_id: int,
        role_id: int,
    ) -> PermissionAssignment:
        """
        Assign a permission level to a role.

        Returns
        -------
        PermissionAssignment
            The newly created permission assignment.
        """
        result = await self.create(
            guild_id=guild_id,
            permission_rank_id=permission_rank_id,
            role_id=role_id,
        )
        if self._backend is not None:
            await self._backend.delete(
                f"{PERM_KEY_PREFIX}permission_assignments:{guild_id}",
            )
        else:
            self._assignments_cache.invalidate(
                f"permission_assignments:{guild_id}",
            )
        logger.trace(f"Invalidated permission assignment cache for guild {guild_id}")
        return result

    async def get_assignments_by_guild(
        self,
        guild_id: int,
    ) -> list[PermissionAssignment]:
        """
        Get all permission assignments for a guild.

        Returns
        -------
        list[PermissionAssignment]
            List of all permission assignments for the guild.
        """
        backend_key = f"{PERM_KEY_PREFIX}permission_assignments:{guild_id}"
        if self._backend is not None:
            raw = await self._backend.get(backend_key)
            if raw is not None and isinstance(raw, list):
                logger.trace(
                    f"Cache hit for permission assignments (guild {guild_id})",
                )
                items = cast(list[dict[str, Any]], raw)
                return [PermissionAssignment.model_validate(d) for d in items]
            if raw is not None:
                logger.warning(
                    "Malformed cache entry for permission assignments (guild {}), "
                    "fetching from DB",
                    guild_id,
                )
        cache_key = f"permission_assignments:{guild_id}"
        if self._backend is None:
            cached = self._assignments_cache.get(cache_key)
            if cached is not None:
                logger.trace(
                    f"Cache hit for permission assignments (guild {guild_id})",
                )
                return cached

        result = await self.find_all(filters=PermissionAssignment.guild_id == guild_id)
        if self._backend is not None:
            await self._backend.set(
                backend_key,
                [m.model_dump() for m in result],
                ttl_sec=PERM_RANKS_TTL,
            )
        else:
            self._assignments_cache.set(cache_key, result)
        logger.trace(f"Cached permission assignments for guild {guild_id}")
        return result

    async def remove_role_assignment(self, guild_id: int, role_id: int) -> bool:
        """
        Remove a permission level assignment from a role.

        Returns
        -------
        bool
            True if removed successfully, False otherwise.
        """
        deleted_count = await self.delete_where(
            filters=(PermissionAssignment.guild_id == guild_id)
            & (PermissionAssignment.role_id == role_id),
        )
        if deleted_count > 0:
            if self._backend is not None:
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}permission_assignments:{guild_id}",
                )
            else:
                self._assignments_cache.invalidate(
                    f"permission_assignments:{guild_id}",
                )
            logger.trace(
                f"Invalidated permission assignment cache for guild {guild_id}",
            )
        return deleted_count > 0

    async def remove_role_assignments_from_rank(
        self,
        guild_id: int,
        permission_rank_id: int,
        role_ids: list[int],
    ) -> int:
        """
        Remove permission level assignments for multiple roles from a single rank.

        Only deletes assignments for the given permission_rank_id, so roles are
        removed from that rank only, not from every rank in the guild.

        Invalidates the permission assignments cache once after all deletions.

        Returns
        -------
        int
            Number of role assignments removed.
        """
        if not role_ids:
            return 0
        deleted_count = await self.delete_where(
            filters=(PermissionAssignment.guild_id == guild_id)
            & (PermissionAssignment.permission_rank_id == permission_rank_id)
            & (PermissionAssignment.role_id.in_(role_ids)),  # type: ignore[attr-defined]
        )
        if deleted_count > 0:
            if self._backend is not None:
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}permission_assignments:{guild_id}",
                )
            else:
                self._assignments_cache.invalidate(
                    f"permission_assignments:{guild_id}",
                )
            logger.trace(
                f"Invalidated permission assignment cache for guild {guild_id}",
            )
        return deleted_count

    async def get_user_permission_rank(  # noqa: PLR0911, PLR0912
        self,
        guild_id: int,
        user_id: int,
        user_roles: list[int],
    ) -> int:
        """
        Get the highest permission rank a user has based on their roles.

        Parameters
        ----------
        guild_id : int
            The guild ID to check permissions for.
        user_id : int
            The user ID (currently unused, kept for API consistency).
        user_roles : list[int]
            List of role IDs the user has.

        Returns
        -------
        int
            The highest permission rank (0 if user has no assigned roles).
        """
        if not user_roles:
            return 0

        sorted_roles = tuple(sorted(user_roles))
        backend_key = (
            f"{PERM_KEY_PREFIX}user_permission_rank:{guild_id}:{user_id}:{sorted_roles}"
        )
        cache_key = f"user_permission_rank:{guild_id}:{user_id}:{sorted_roles}"
        if self._backend is not None:
            raw = await self._backend.get(backend_key)
            if raw is not None and isinstance(raw, int):
                logger.trace(
                    f"Cache hit for user permission rank (guild {guild_id}, user {user_id})",
                )
                return raw
        else:
            cached = self._user_rank_cache.get(cache_key)
            if cached is not None:
                logger.trace(
                    f"Cache hit for user permission rank (guild {guild_id}, user {user_id})",
                )
                return cached

        # Get all permission assignments for this guild (uses cache)
        assignments = await self.get_assignments_by_guild(guild_id)
        if not assignments:
            if self._backend is not None:
                await self._backend.set(
                    backend_key,
                    0,
                    ttl_sec=PERM_USER_RANK_TTL,
                )
            else:
                self._user_rank_cache.set(cache_key, 0)
            return 0

        max_rank = 0
        assigned_role_ids = {assignment.role_id for assignment in assignments}
        user_assigned_roles = set(user_roles) & assigned_role_ids
        if not user_assigned_roles:
            if self._backend is not None:
                await self._backend.set(
                    backend_key,
                    0,
                    ttl_sec=PERM_USER_RANK_TTL,
                )
            else:
                self._user_rank_cache.set(cache_key, 0)
            return 0

        permission_rank_ids = {
            assignment.permission_rank_id
            for assignment in assignments
            if assignment.role_id in user_assigned_roles
        }
        if not permission_rank_ids:
            if self._backend is not None:
                await self._backend.set(
                    backend_key,
                    0,
                    ttl_sec=PERM_USER_RANK_TTL,
                )
            else:
                self._user_rank_cache.set(cache_key, 0)
            return 0

        async with self.db.session() as session:
            stmt = (
                select(PermissionRank).where(PermissionRank.id.in_(permission_rank_ids))  # type: ignore[attr-defined]
            )
            result = await session.execute(stmt)
            rank_records = list(result.scalars().all())
            for rank_record in rank_records:
                session.expunge(rank_record)

        for rank_record in rank_records:
            if rank_record.rank > max_rank:
                max_rank = int(rank_record.rank)

        if self._backend is not None:
            await self._backend.set(
                backend_key,
                max_rank,
                ttl_sec=PERM_USER_RANK_TTL,
            )
        else:
            self._user_rank_cache.set(cache_key, max_rank)
        logger.trace(
            f"Cached user permission rank {max_rank} for guild {guild_id}, user {user_id}",
        )
        return max_rank


def wrap_optional_perm(value: PermissionCommand | None) -> dict[str, Any]:
    """Wrap optional PermissionCommand for backend (distinguish cached None from miss)."""
    return {"_v": value.model_dump() if value is not None else None}


def unwrap_optional_perm(raw: Any) -> PermissionCommand | None:
    """Unwrap optional PermissionCommand from backend."""
    if raw is None or not isinstance(raw, dict):
        return None
    raw_dict = cast(dict[str, Any], raw)
    v = raw_dict.get("_v")
    if v is None:
        return None
    return PermissionCommand.model_validate(v)


class PermissionCommandController(BaseController[PermissionCommand]):
    """Controller for managing command permission requirements."""

    # Shared cache when no backend
    _command_permissions_cache: TTLCache = TTLCache(ttl=PERM_RANKS_TTL, max_size=2000)

    def __init__(
        self,
        db: DatabaseService | None = None,
        cache_backend: AsyncCacheBackendProtocol | None = None,
    ) -> None:
        """Initialize the guild command permission controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        cache_backend : AsyncCacheBackendProtocol | None, optional
            Optional cache backend (Valkey/in-memory) for command permissions.
        """
        super().__init__(PermissionCommand, db)
        self._backend = cache_backend

    async def set_command_permission(
        self,
        guild_id: int,
        command_name: str,
        required_rank: int,
        description: str | None = None,
    ) -> (
        PermissionCommand
    ):  # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
        """
        Set the permission rank required for a command.

        Returns
        -------
        PermissionCommand
            The command permission record (created or updated).
        """
        result = await self.upsert(
            filters={"guild_id": guild_id, "command_name": command_name},
            guild_id=guild_id,
            command_name=command_name,
            required_rank=required_rank,
            description=description,
        )
        if self._backend is not None:
            await self._backend.delete(
                f"{PERM_KEY_PREFIX}command_permission:{guild_id}:{command_name}",
            )
            parts = command_name.split()
            for i in range(len(parts) - 1, 0, -1):
                parent_name = " ".join(parts[:i])
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}command_permission:{guild_id}:{parent_name}",
                )
        else:
            cache_key = f"command_permission:{guild_id}:{command_name}"
            self._command_permissions_cache.invalidate(cache_key)
            parts = command_name.split()
            for i in range(len(parts) - 1, 0, -1):
                parent_name = " ".join(parts[:i])
                parent_cache_key = f"command_permission:{guild_id}:{parent_name}"
                self._command_permissions_cache.invalidate(parent_cache_key)
        logger.trace(
            f"Invalidated command permission cache for {command_name} (guild {guild_id})",
        )
        return result[0]  # upsert returns (record, created)

    async def invalidate_command_permission(
        self,
        guild_id: int,
        command_name: str,
    ) -> None:
        """
        Invalidate the command permission cache for a command and its parents.

        Call after removing a command permission (e.g. delete_where) so the next
        get_command_permission sees fresh data.

        Notes
        -----
        This invalidates only the controller cache (PERM_KEY_PREFIX). Callers that
        use PermissionSystem.get_command_permission must also call
        PermissionSystem.invalidate_command_permission_cache so the fallback cache
        (PERM_FALLBACK_KEY_PREFIX) is cleared; both layers must be invalidated
        together after a database change.
        """
        if self._backend is not None:
            await self._backend.delete(
                f"{PERM_KEY_PREFIX}command_permission:{guild_id}:{command_name}",
            )
            parts = command_name.split()
            for i in range(len(parts) - 1, 0, -1):
                parent_name = " ".join(parts[:i])
                await self._backend.delete(
                    f"{PERM_KEY_PREFIX}command_permission:{guild_id}:{parent_name}",
                )
        else:
            cache_key = f"command_permission:{guild_id}:{command_name}"
            self._command_permissions_cache.invalidate(cache_key)
            parts = command_name.split()
            for i in range(len(parts) - 1, 0, -1):
                parent_name = " ".join(parts[:i])
                parent_cache_key = f"command_permission:{guild_id}:{parent_name}"
                self._command_permissions_cache.invalidate(parent_cache_key)
        logger.trace(
            f"Invalidated command permission cache for {command_name} (guild {guild_id})",
        )

    async def get_command_permission(
        self,
        guild_id: int,
        command_name: str,
    ) -> PermissionCommand | None:
        """
        Get the permission requirement for a specific command.

        Returns
        -------
        PermissionCommand | None
            The command permission record if found, None otherwise.
        """
        backend_key = f"{PERM_KEY_PREFIX}command_permission:{guild_id}:{command_name}"
        cache_key = f"command_permission:{guild_id}:{command_name}"
        if self._backend is not None:
            raw = await self._backend.get(backend_key)
            if raw is not None:
                logger.trace(
                    f"Cache hit for command permission {command_name} (guild {guild_id})",
                )
                return unwrap_optional_perm(raw)
        else:
            cached = self._command_permissions_cache.get(cache_key)
            if cached is not None:
                logger.trace(
                    f"Cache hit for command permission {command_name} (guild {guild_id})",
                )
                return unwrap_optional_perm(cached)

        result = await self.find_one(
            filters=(PermissionCommand.guild_id == guild_id)
            & (PermissionCommand.command_name == command_name),
        )
        wrapped = wrap_optional_perm(result)
        if self._backend is not None:
            await self._backend.set(
                backend_key,
                wrapped,
                ttl_sec=PERM_RANKS_TTL,
            )
        else:
            self._command_permissions_cache.set(cache_key, wrapped)
        logger.trace(f"Cached command permission for {command_name} (guild {guild_id})")
        return result

    async def get_all_command_permissions(
        self,
        guild_id: int,
    ) -> list[PermissionCommand]:
        """
        Get all command permissions for a guild.

        Returns
        -------
        list[PermissionCommand]
            List of all command permissions ordered by name.
        """
        return await self.find_all(
            filters=PermissionCommand.guild_id == guild_id,
            order_by=PermissionCommand.command_name,
        )
