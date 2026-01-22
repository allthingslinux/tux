"""Discord.py command converters for Tux bot.

This module provides custom converters for parsing command arguments,
including time durations, case types, and utility functions for channel
resolution and boolean conversion.
"""

from __future__ import annotations

import contextlib
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
    "FlexibleUserConverter",
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


class FlexibleUserConverter(commands.Converter[discord.User]):
    """Convert various user representations to discord.User.

    Accepts user mentions, user IDs (snowflakes), and usernames.
    Tries multiple conversion methods in order:
    1. Standard UserConverter (handles mentions and username#discriminator)
    2. Direct user ID lookup (for raw snowflake IDs)
    """

    async def convert(self, ctx: commands.Context[Any], argument: str) -> discord.User:
        """
        Convert a string to a discord.User.

        Parameters
        ----------
        ctx : commands.Context[Any]
            The invocation context.
        argument : str
            The user identifier (mention, ID, or username).

        Returns
        -------
        discord.User
            The user object.

        Raises
        ------
        commands.BadArgument
            If the user cannot be found or the argument is invalid.
        """
        # First, try the standard UserConverter (handles mentions, username#discriminator)
        with contextlib.suppress(commands.UserNotFound):
            return await commands.UserConverter().convert(ctx, argument)

        # If that fails, try treating it as a raw user ID
        with contextlib.suppress(ValueError):
            user_id = int(argument)
            # Validate it's a reasonable Discord snowflake (15-20 digits)
            if not (15 <= len(argument) <= 20):
                msg = f"Invalid user ID format: {argument}"
                raise commands.BadArgument(msg)

            # Try to fetch the user by ID from cache first
            if user := ctx.bot.get_user(user_id):
                return user

            # If not in cache, try fetching from Discord
            try:
                return await ctx.bot.fetch_user(user_id)
            except discord.NotFound:
                msg = f"User with ID {user_id} not found."
                raise commands.BadArgument(msg) from None
            except discord.HTTPException as e:
                msg = f"Error fetching user {user_id}: {e}"
                raise commands.BadArgument(msg) from e

        # Not a valid integer, so it's not a user ID
        msg = f"User '{argument}' not found. Try using a mention, user ID, or username#discriminator."
        raise commands.BadArgument(msg)


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
