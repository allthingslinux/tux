"""
Utility Module for Tux Bot.

This module provides common utility functions and helpers used throughout
the Tux bot, including AFK management and shared functionality.
"""

import contextlib
from datetime import datetime

import discord

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
        await target.edit(nick=new_name)


async def del_afk(
    db: DatabaseCoordinator,
    target: discord.Member,
    nickname: str,
) -> None:
    """Remove a member's AFK status, restores their nickname, and updates the database."""
    await db.afk.remove_afk(target.id, target.guild.id)

    # Suppress Forbidden errors if the bot doesn't have permission to change the nickname
    with contextlib.suppress(discord.Forbidden):
        # Only attempt to restore nickname if it was actually changed by add_afk
        # Prevents resetting a manually changed nickname if del_afk is called unexpectedly
        if target.display_name.startswith(AFK_PREFIX):
            await target.edit(nick=nickname)
