import contextlib
from datetime import datetime
from types import NoneType

import discord
from database.controllers import DatabaseController
from utils.constants import CONST

__all__ = ("add_afk", "del_afk")


def _generate_afk_nickname(display_name: str) -> str:
    """Generates the AFK nickname, handling truncation if necessary."""
    prefix_len = len(CONST.AFK_PREFIX)

    if len(display_name) >= CONST.NICKNAME_MAX_LENGTH - prefix_len:
        suffix_len = len(CONST.AFK_TRUNCATION_SUFFIX)
        available_space = CONST.NICKNAME_MAX_LENGTH - prefix_len - suffix_len
        truncated_name = f"{display_name[:available_space]}{CONST.AFK_TRUNCATION_SUFFIX}"

        return f"{CONST.AFK_PREFIX}{truncated_name}"

    return f"{CONST.AFK_PREFIX}{display_name}"


async def add_afk(
    db: DatabaseController,
    reason: str,
    target: discord.Member,
    guild_id: int,
    is_perm: bool,
    until: datetime | NoneType | None = None,
    enforced: bool = False,
) -> None:
    """Sets a member as AFK, updates their nickname, and saves to the database."""
    new_name = _generate_afk_nickname(target.display_name)

    await db.afk.set_afk(target.id, target.display_name, reason, guild_id, is_perm, until, enforced)

    # Suppress Forbidden errors if the bot doesn't have permission to change the nickname
    with contextlib.suppress(discord.Forbidden):
        await target.edit(nick=new_name)


async def del_afk(db: DatabaseController, target: discord.Member, nickname: str) -> None:
    """Removes a member's AFK status, restores their nickname, and updates the database."""
    await db.afk.remove_afk(target.id)

    # Suppress Forbidden errors if the bot doesn't have permission to change the nickname
    with contextlib.suppress(discord.Forbidden):
        # Only attempt to restore nickname if it was actually changed by add_afk
        # Prevents resetting a manually changed nickname if del_afk is called unexpectedly
        if target.display_name.startswith(CONST.AFK_PREFIX):
            await target.edit(nick=nickname)
