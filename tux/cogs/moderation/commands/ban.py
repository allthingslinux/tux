from __future__ import annotations

import discord
from prisma.enums import CaseType

from ..command_meta import ModerationCommand


class Ban(ModerationCommand):
    """Ban a member from the server."""

    name = "ban"
    aliases = ["b"]
    description = "Ban a member from the server."
    case_type = CaseType.BAN
    required_pl = 3
    dm_action = "banned"

    flags = {
        "purge": dict(type=int, aliases=["p"], default=0, desc="Days of messages to delete (0-7)"),
        "silent": dict(type=bool, aliases=["s", "quiet"], default=False, desc="Don't DM the target"),
    }

    async def _action(self, guild: discord.Guild, member: discord.Member | discord.User, *, flags, reason: str) -> None:
        await guild.ban(member, reason=reason, delete_message_seconds=flags.purge * 86_400)


# Extension entrypoint (no-op, handled by metaclass)
async def setup(bot):  # type: ignore[unused-argument]
    return