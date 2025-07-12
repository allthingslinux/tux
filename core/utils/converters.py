import re
from typing import Any, cast

import discord
from bot import Tux
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType

time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter[float]):
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
    async def convert(self, ctx: commands.Context[Any], argument: str) -> CaseType:
        """
        Convert a string to a CaseType enum.

        Parameters
        ----------
        ctx : commands.Context[Any]
            The context to convert the argument to a CaseType enum.
        argument : str
            The argument to convert to a CaseType enum.

        Returns
        -------
        CaseType
            The CaseType enum.
        """

        try:
            return CaseType[argument.upper()]
        except KeyError as e:
            msg = f"Invalid CaseType: {argument}"
            raise commands.BadArgument(msg) from e


async def get_channel_safe(bot: Tux, channel_id: int) -> discord.TextChannel | discord.Thread | None:
    """Get a channel by ID, returning None if not found."""
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            logger.error(f"Channel not found for ID: {channel_id}")
            return None
        except (discord.Forbidden, discord.HTTPException) as fetch_error:
            logger.error(f"Failed to fetch channel: {fetch_error}")
            return None
    return cast(discord.TextChannel | discord.Thread, channel)


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
