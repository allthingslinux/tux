"""Discord.py command converters for Tux bot.

This module provides custom converters for parsing command arguments,
including time durations, case types, and utility functions for channel
resolution and boolean conversion.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands
from loguru import logger

from tux.database.models import CaseType

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = [
    # Converters
    "TimeConverter",
    "CaseTypeConverter",
    # Utility functions
    "get_channel_safe",
    "convert_bool",
]

time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter[float]):
    """Convert string representations of time durations to seconds.

    Supports time units: s (seconds), m (minutes), h (hours), d (days).
    Examples: "1h30m", "2d", "45s", "1.5h".
    """

    async def convert(self, ctx: commands.Context[Any], argument: str) -> float:
        """
        Convert a string representation of time (e.g., "1h30m", "2d") into seconds.

        Parameters
        ----------
        ctx : commands.Context[Any]
            The invocation context.
        argument : str
            The time string to convert.

        Returns
        -------
        float
            The total time in seconds.

        Raises
        ------
        commands.BadArgument
            If the time string format is invalid or uses invalid units.
        """
        matches = time_regex.findall(argument.lower())
        time = 0.0
        if not matches:
            msg = "Invalid time format. Use digits followed by s, m, h, or d (e.g., '1h30m')."
            raise commands.BadArgument(msg)

        for v, k in matches:
            try:
                # Replace comma with dot for float conversion if necessary
                processed_v = v.replace(",", ".")
                time += time_dict[k] * float(processed_v)
            except KeyError as e:
                msg = f"'{k}' is an invalid time unit. Use s, m, h, or d."
                raise commands.BadArgument(msg) from e
            except ValueError as e:
                msg = f"Could not convert '{v}' to a number."
                raise commands.BadArgument(msg) from e
        return time


class CaseTypeConverter(commands.Converter[CaseType]):
    """Convert string representations to CaseType enum values.

    Accepts case type names (case-insensitive) and converts them to
    the corresponding CaseType enum value for moderation commands.
    """

    async def convert(self, ctx: commands.Context[Any], argument: str) -> CaseType:
        """
        Convert a string to a CaseType enum.

        Parameters
        ----------
        ctx : commands.Context[Any]
            The invocation context.
        argument : str
            The string to convert.

        Returns
        -------
        CaseType
            The CaseType enum value.

        Raises
        ------
        commands.BadArgument
            If the argument is not a valid CaseType.
        """
        try:
            return CaseType[argument.upper()]
        except KeyError as e:
            msg = f"Invalid CaseType: {argument}"
            raise commands.BadArgument(msg) from e


async def get_channel_safe(
    bot: Tux,
    channel_id: int,
) -> discord.TextChannel | discord.Thread | None:
    """
    Get a TextChannel or Thread by ID, returning None if not found.

    This narrows the return type so callers can safely use fetch_message and message.reactions.

    Returns
    -------
    discord.TextChannel | discord.Thread | None
        The channel if found and is a text channel or thread, None otherwise.
    """
    try:
        channel = bot.get_channel(channel_id)
    except Exception as e:
        logger.opt(exception=e).error(f"Error getting channel {channel_id}")
        return None
    else:
        if isinstance(channel, discord.TextChannel | discord.Thread):
            return channel
        return None


def convert_bool(x: str | None) -> bool | None:
    """Convert a string to a boolean value.

    Parameters
    ----------
    x : str | None
        The string to convert.

    Returns
    -------
    bool | None
        The converted boolean value, or None if x is None.

    Raises
    ------
    commands.BadArgument
        If the string cannot be converted to a boolean.
    """
    if x is None:
        return None

    x = str(x).lower()

    if x in {"true", "t", "yes", "y", "1", "on", "active", "enable", "enabled"}:
        return True
    if x in {"false", "f", "no", "n", "0", "off", "inactive", "disable", "disabled"}:
        return False

    msg = f"{x} must be a boolean value (e.g. true/false, yes/no)"
    raise commands.BadArgument(msg)
