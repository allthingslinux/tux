"""
Rank management utilities for the config dashboard.

Provides utilities for creating and managing permission ranks
in the unified configuration dashboard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from tux.core.permission_system import DEFAULT_RANKS
from tux.services.sentry import capture_exception_safe

if TYPE_CHECKING:
    from tux.database.controllers import DatabaseCoordinator


async def initialize_default_ranks(db: DatabaseCoordinator, guild_id: int) -> None:
    """
    Initialize default permission ranks (0-7) for a guild.

    This creates the standard permission hierarchy that guilds can customize.
    If ranks already exist, this function does nothing (idempotent).

    Parameters
    ----------
    db : DatabaseCoordinator
        Database coordinator instance
    guild_id : int
        Discord guild ID to initialize ranks for

    Notes
    -----
    Uses the authoritative default ranks from the permission system to ensure
    consistency across all initialization methods.
    """
    logger.debug(f"initialize_default_ranks called for guild {guild_id}")

    # Ensure guild is registered in database first
    logger.debug(f"Ensuring guild {guild_id} is registered in database")
    guild_record = await db.guild.get_by_id(guild_id)
    if not guild_record:
        logger.info(f"Guild {guild_id} not found in database, registering it")
        try:
            await db.guild.insert_guild_by_id(guild_id)
            logger.success(f"Successfully registered guild {guild_id}")
        except Exception as reg_error:
            logger.error(f"Failed to register guild {guild_id}: {reg_error}")
            raise

    # Check if ranks already exist (idempotent check)
    logger.trace(f"Checking existing ranks for guild {guild_id}")
    try:
        existing_ranks = await db.permission_ranks.get_permission_ranks_by_guild(
            guild_id,
        )
        logger.trace(f"Found {len(existing_ranks)} existing ranks")
        if existing_ranks:
            logger.info(f"Guild {guild_id} already has ranks, skipping initialization")
            return
    except Exception as e:
        logger.error(f"Error checking existing ranks for guild {guild_id}: {e}")
        capture_exception_safe(
            e,
            extra_context={
                "operation": "check_existing_ranks",
                "guild_id": str(guild_id),
            },
        )
        raise

    # Create the default ranks
    logger.info(f"Creating {len(DEFAULT_RANKS)} default ranks for guild {guild_id}")
    for rank, data in DEFAULT_RANKS.items():
        logger.trace(f"Creating rank {rank} with data: {data}")
        try:
            await db.permission_ranks.create_permission_rank(
                guild_id=guild_id,
                rank=rank,
                name=data["name"],
                description=data["description"],
            )
        except Exception as e:
            logger.error(f"Error creating rank {rank} for guild {guild_id}: {e}")
            logger.error(f"Rank data: {data}")
            capture_exception_safe(
                e,
                extra_context={
                    "operation": "create_permission_rank",
                    "guild_id": str(guild_id),
                    "rank": str(rank),
                    "rank_name": data.get("name"),
                },
            )
            raise
        else:
            logger.debug(f"Successfully created rank {rank} for guild {guild_id}")

    logger.success(f"Successfully created all default ranks for guild {guild_id}")
