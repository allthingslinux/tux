"""
Command and Interaction Context Utilities.

This module provides helper functions to abstract and normalize the process of
extracting contextual information from different types of command invocations
in `discord.py`.

The primary goal is to create a single, consistent dictionary format for context
data, regardless of whether the command was triggered by a traditional prefix
command (`commands.Context`) or a slash command (`discord.Interaction`).
This standardized context is invaluable for logging, error reporting (e.g., to
Sentry), and any other system that needs to operate on command data without
worrying about the source type.
"""

from __future__ import annotations

from typing import Any

from discord import Interaction
from discord.ext import commands

# Type alias for a command context or an interaction.
ContextOrInteraction = commands.Context[Any] | Interaction


def _get_interaction_details(source: Interaction) -> dict[str, Any]:
    """
    Extracts context details specifically from a discord.Interaction.

    Parameters
    ----------
    source : Interaction
        The interaction object from a slash command.

    Returns
    -------
    dict[str, Any]
        A dictionary containing interaction-specific context.
    """
    details: dict[str, Any] = {
        "command_type": "slash",
        "interaction_id": source.id,
        "channel_id": source.channel_id,
        "guild_id": source.guild_id,
    }
    if source.command:
        details["command_name"] = source.command.qualified_name
    return details


def _get_context_details(source: commands.Context[Any]) -> dict[str, Any]:
    """
    Extracts context details specifically from a commands.Context.

    Parameters
    ----------
    source : commands.Context[Any]
        The context object from a prefix command.

    Returns
    -------
    dict[str, Any]
        A dictionary containing context-specific data.
    """
    details: dict[str, Any] = {
        "command_type": "prefix",
        "message_id": source.message.id,
        "channel_id": source.channel.id,
        "guild_id": source.guild.id if source.guild else None,
    }
    if source.command:
        details["command_name"] = source.command.qualified_name
        details["command_prefix"] = source.prefix
        details["command_invoked_with"] = source.invoked_with
    return details


def get_interaction_context(source: ContextOrInteraction) -> dict[str, Any]:
    """
    Builds a standardized dictionary of context from a command or interaction.

    This is the main public function of the module. It takes either a
    `commands.Context` or a `discord.Interaction` and returns a dictionary
    with a consistent set of keys, abstracting away the differences between
    the two source types.

    Args:
        source: The command `Context` or `Interaction` object.

    Returns
    -------
        A dictionary with standardized context keys like `user_id`,
        `command_name`, `guild_id`, `command_type`, etc.
    """
    # Safely get the user/author attribute; fall back to None
    user = getattr(source, "user", None) if isinstance(source, Interaction) else getattr(source, "author", None)

    # Base context is common to both types
    context: dict[str, Any] = {
        "user_id": getattr(user, "id", None),
        "user_name": str(user) if user is not None else "Unknown",
        "is_interaction": isinstance(source, Interaction),
    }

    # Delegate to helper functions for type-specific details
    details = _get_interaction_details(source) if isinstance(source, Interaction) else _get_context_details(source)
    context |= details

    return context
