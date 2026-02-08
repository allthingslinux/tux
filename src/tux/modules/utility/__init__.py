"""
Utility Module for Tux Bot.

This module provides common utility functions and helpers used throughout
the Tux bot, including AFK management and shared functionality.
"""

import contextlib
from datetime import datetime

import discord
from loguru import logger

from tux.database.controllers import DatabaseCoordinator
from tux.shared.constants import AFK_PREFIX, NICKNAME_MAX_LENGTH, TRUNCATION_SUFFIX

__all__ = ("add_afk", "del_afk")


def _generate_afk_nickname(display_name: str) -> str:
    """
    Generate the AFK nickname, handling truncation if necessary.

    Returns
    -------
    str
        The AFK nickname with [AFK] prefix.
    """
    prefix_len = len(AFK_PREFIX)

    if len(display_name) >= NICKNAME_MAX_LENGTH - prefix_len:
        suffix_len = len(TRUNCATION_SUFFIX)
        available_space = NICKNAME_MAX_LENGTH - prefix_len - suffix_len
        truncated_name = f"{display_name[:available_space]}{TRUNCATION_SUFFIX}"

        return f"{AFK_PREFIX}{truncated_name}"

    return f"{AFK_PREFIX}{display_name}"


async def add_afk(
    db: DatabaseCoordinator,
    reason: str,
    target: discord.Member,
    guild_id: int,
    is_perm: bool,
    until: datetime | None = None,
    enforced: bool = False,
) -> None:
    """Set a member as AFK, updates their nickname, and saves to the database."""
    new_name = _generate_afk_nickname(target.display_name)

    await db.afk.set_afk(
        target.id,
        target.display_name,
        reason,
        guild_id,
        is_perm,
        until,
        enforced,
    )

    # Suppress Forbidden errors if the bot doesn't have permission to change the nickname
    with contextlib.suppress(discord.Forbidden):
        logger.info(
            f"Setting AFK nickname for {target.id}: '{target.display_name}' -> '{new_name}'",
        )
        await target.edit(nick=new_name)


async def del_afk(
    db: DatabaseCoordinator,
    target: discord.Member,
    nickname: str,
) -> None:
    """Remove a member's AFK status, restores their nickname, and updates the database.

    Parameters
    ----------
    db : DatabaseCoordinator
        The database coordinator instance.
    target : discord.Member
        The member whose AFK status should be removed. Must be a Member (not User).
    nickname : str
        The original nickname to restore.

    Raises
    ------
    AttributeError
        If target is not a Member or doesn't have a guild attribute.
    """
    # Validate that target is a Member with a guild (runtime check for callers)
    if not isinstance(target, discord.Member) or target.guild is None:  # type: ignore[reportUnnecessaryIsInstance, reportUnnecessaryComparison]
        msg = f"target must be a discord.Member with a guild, got {type(target)}"
        raise AttributeError(msg)

    # Restore nickname first before removing from database
    # This ensures if nickname restore fails, AFK entry still exists
    with contextlib.suppress(discord.Forbidden):
        # Only attempt to restore nickname if it was actually changed by add_afk
        # Prevents resetting a manually changed nickname if del_afk is called unexpectedly
        if target.display_name.startswith(AFK_PREFIX):
            logger.info(
                f"Restoring nickname for {target.id}: '{target.display_name}' -> '{nickname}'",
            )
            await target.edit(nick=nickname)
        else:
            logger.debug(
                f"Skipping nickname restore for {target.id} (doesn't have AFK prefix)",
            )

    # Remove from database after nickname is restored (or attempted)
    await db.afk.remove_afk(target.id, target.guild.id)
