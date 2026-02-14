"""
Command discovery utilities for ConfigDashboard.

Provides functions to discover and filter commands that use the permission
decorator for the command permissions UI (moderation, levels/XP, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tux.core.permission_system import RESTRICTED_COMMANDS

if TYPE_CHECKING:
    from tux.core.bot import Tux

# Module name substrings: cogs in these modules are included in the config
# command permissions list (e.g. moderation, levels/lvls/XP/blacklist).
_PERMISSION_COG_MODULES = ("moderation", "levels")

# Commands from those modules that do not use @requires_command_permission()
# and must not appear in the permission assignment UI (e.g. level is view-only).
_EXCLUDED_FROM_PERMISSION_ASSIGNMENT = frozenset({"level"})


def get_moderation_commands(bot: Tux) -> list[str]:
    """
    Discover all command names that use the permission decorator from loaded cogs.

    Only includes the main command name, not aliases. Commands are discovered
    from cogs whose module contains "moderation" or "levels" (covers moderation
    commands and level/XP/blacklist management). Restricted commands
    (owner/sysadmin only) are automatically excluded.

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

    # Discover commands from loaded cogs (moderation and levels)
    for cog in bot.cogs.values():
        module_name = cog.__class__.__module__
        if any(part in module_name.lower() for part in _PERMISSION_COG_MODULES):
            for command in cog.get_commands():
                # Only add the main command name, not aliases
                # Exclude restricted commands (owner/sysadmin only)
                # Exclude commands that don't use the permission decorator (e.g. level is view-only)
                if (
                    command.name.lower() not in RESTRICTED_COMMANDS
                    and command.name.lower() not in _EXCLUDED_FROM_PERMISSION_ASSIGNMENT
                ):
                    command_names.add(command.name)

    # Fallback: Known commands that require permission assignment
    # Only includes main command names (not aliases)
    known_commands = {
        # Moderation
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
        "togglesnippetlock",  # aliases: tsl
        "clearafk",  # aliases: unafk
        # Levels / XP / blacklist (levels set, setxp, reset, blacklist)
        "levels",  # aliases: lvls
        # Note: "report" command does not use @requires_command_permission()
        # so it's excluded from permission assignment
    }

    # Add known commands as fallback, excluding restricted commands
    command_names.update(
        cmd for cmd in known_commands if cmd.lower() not in RESTRICTED_COMMANDS
    )

    return sorted(command_names)
