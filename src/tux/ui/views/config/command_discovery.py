"""
Command discovery utilities for ConfigDashboard.

Provides functions to discover and filter moderation commands
for the command permissions UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tux.core.permission_system import RESTRICTED_COMMANDS

if TYPE_CHECKING:
    from tux.core.bot import Tux


def get_moderation_commands(bot: Tux) -> list[str]:
    """
    Discover all moderation command names from loaded cogs.

    Only includes the main command name, not aliases.
    Commands are discovered by checking if the cog's module contains "moderation".
    Restricted commands (owner/sysadmin only) are automatically excluded.

    Parameters
    ----------
    bot : Tux
        The bot instance

    Returns
    -------
    list[str]
        Sorted list of unique command names (restricted commands excluded)
    """
    command_names: set[str] = set()

    # Discover commands from loaded cogs
    for cog in bot.cogs.values():
        # Check if cog's module contains "moderation"
        module_name = cog.__class__.__module__
        if "moderation" in module_name.lower():
            for command in cog.get_commands():
                # Only add the main command name, not aliases
                # Exclude restricted commands (owner/sysadmin only)
                if command.name.lower() not in RESTRICTED_COMMANDS:
                    command_names.add(command.name)

    # Fallback: Known moderation commands if discovery fails
    # Only includes main command names (not aliases) that require permission assignment
    known_commands = {
        "ban",  # aliases: b
        "unban",  # aliases: ub
        "kick",  # aliases: k
        "timeout",  # aliases: to, mute
        "untimeout",  # aliases: uto, unmute
        "warn",  # aliases: w
        "cases",  # aliases: case, c (group command)
        "purge",  # aliases: p
        "slowmode",  # aliases: sm
        "jail",  # aliases: j
        "unjail",  # aliases: uj
        "tempban",  # aliases: tb
        "pollban",  # aliases: pb
        "pollunban",  # aliases: pub
        "snippetban",  # aliases: sb
        "snippetunban",  # aliases: sub
        "clearafk",  # aliases: unafk
        # Note: "report" command does not use @requires_command_permission()
        # so it's excluded from permission assignment
    }

    # Add known commands as fallback, excluding restricted commands
    command_names.update(
        cmd for cmd in known_commands if cmd.lower() not in RESTRICTED_COMMANDS
    )

    return sorted(command_names)
