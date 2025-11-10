"""
Command discovery utilities for ConfigDashboard.

Provides functions to discover and filter moderation commands
for the command permissions UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tux.core.bot import Tux


def get_moderation_commands(bot: Tux) -> list[str]:
    """
    Discover all moderation command names from loaded cogs.

    Only includes the main command name, not aliases.
    Commands are discovered by checking if the cog's module contains "moderation".

    Parameters
    ----------
    bot : Tux
        The bot instance

    Returns
    -------
    list[str]
        Sorted list of unique command names
    """
    command_names: set[str] = set()

    # Discover commands from loaded cogs
    for cog in bot.cogs.values():
        # Check if cog's module contains "moderation"
        module_name = cog.__class__.__module__
        if "moderation" in module_name.lower():
            for command in cog.get_commands():
                # Only add the main command name, not aliases
                command_names.add(command.name)

    # Fallback: Known moderation commands if discovery fails
    known_commands = {
        "ban",
        "unban",
        "kick",
        "timeout",
        "warn",
        "case",
        "cases",
        "modlogs",
        "purge",
        "slowmode",
        "lock",
        "unlock",
    }

    # Add known commands as fallback
    command_names.update(known_commands)

    return sorted(command_names)
