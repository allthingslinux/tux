"""
Shared Utility Functions for Tux Bot.

This module contains common utility functions used throughout the Tux Discord bot,
including text processing, time conversion, parameter validation, and documentation
formatting utilities.
"""

import inspect
import re
from datetime import timedelta
from typing import Any, Union, get_args, get_origin

from discord.ext import commands

__all__ = [
    "convert_to_seconds",
    "docstring_parameter",
    "generate_usage",
    "get_matching_string",
    "is_optional_param",
    "parse_time_string",
    "seconds_to_human_readable",
    "strip_formatting",
    "truncate",
]


def truncate(text: str, length: int) -> str:
    """Truncate a string to a specified length.

    If the string is longer than the specified length, it will be truncated
    and an ellipsis will be appended. Otherwise, the original string is returned.

    Parameters
    ----------
    text : str
        The string to truncate.
    length : int
        The maximum length of the string.

    Returns
    -------
    str
        The truncated string.
    """
    return text if len(text) <= length else f"{text[: length - 3]}..."


def strip_formatting(content: str) -> str:
    """
    Strip formatting from a string.

    Parameters
    ----------
    content : str
        The string to strip formatting from.

    Returns
    -------
    str
        The string with formatting stripped.
    """
    # Remove triple backtick blocks
    content = re.sub(r"```(.*?)```", r"\1", content)
    # Remove single backtick code blocks
    content = re.sub(r"`([^`]*)`", r"\1", content)
    # Remove Markdown headers
    content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)
    # Remove markdown formatting characters, but preserve |
    content = re.sub(r"[\*_~>]", "", content)
    # Remove extra whitespace
    content = re.sub(r"\s+", " ", content)

    return content.strip()


def parse_time_string(time_str: str) -> timedelta:
    """
    Convert a string representation of time into a datetime.timedelta object.

    Parameters
    ----------
    time_str : str
        The string representation of time to convert. (e.g., '60s', '1m', '2h', '10d')

    Returns
    -------
    timedelta
        The timedelta object representing the time string.

    Raises
    ------
    ValueError
        If the time format is invalid.
    """
    # Define regex pattern to parse time strings
    time_pattern = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])$")

    # Match the input string with the pattern
    match = time_pattern.match(time_str)

    if not match:
        msg = f"Invalid time format: '{time_str}'"
        raise ValueError(msg)

    # Extract the value and unit from the pattern match
    value = int(match["value"])
    unit = match["unit"]

    # Define the mapping of units to keyword arguments for timedelta
    unit_map = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}

    # Check if the unit is in the map
    if unit not in unit_map:
        msg = f"Unknown time unit: '{unit}'"
        raise ValueError(msg)

    # Create the timedelta with the appropriate keyword argument
    kwargs = {unit_map[unit]: value}

    return timedelta(**kwargs)


def convert_to_seconds(time_str: str) -> int:
    """
    Convert a formatted time string with the formats Mwdhms.

    Parameters
    ----------
    time_str : str
        The formatted time string to convert to total seconds.

    Returns
    -------
    int
        The total seconds from the formatted time string. Returns 0 if the format is invalid.
    """
    # Time conversion factors from units to seconds
    time_units = {
        "mo": 2592000,  # Months to seconds
        "mnths": 2592000,  # Months to seconds
        "month": 2592000,  # Months to seconds
        "months": 2592000,  # Months to seconds
        "W": 604800,  # Weeks to seconds
        "w": 604800,  # Weeks to seconds
        "wk": 604800,  # Weeks to seconds
        "wks": 604800,  # Weeks to seconds
        "week": 604800,  # Weeks to seconds
        "weeks": 604800,  # Weeks to seconds
        "D": 86400,  # Days to seconds
        "d": 86400,  # Days to seconds
        "day": 86400,  # Days to seconds
        "days": 86400,  # Days to seconds
        "H": 3600,  # Hours to seconds
        "h": 3600,  # Hours to seconds
        "hr": 3600,  # Hours to seconds
        "hrs": 3600,  # Hours to seconds
        "hours": 3600,  # Hours to seconds
        "m": 60,  # Minutes to seconds
        "min": 60,  # Minutes to seconds
        "mins": 60,  # Minutes to seconds
        "minutes": 60,  # Minutes to seconds
        "s": 1,  # Seconds to seconds
        "sec": 1,  # Seconds to seconds
        "secs": 1,  # Seconds to seconds
        "seconds": 1,  # Seconds to seconds
    }

    total_seconds = 0
    current_value = 0

    for char in time_str:
        if char.isdigit():
            # Build the current number
            current_value = current_value * 10 + int(char)
        elif char in time_units:
            # If the unit is known, update total_seconds
            if current_value == 0:
                return (
                    0  # No number specified for the unit, thus treat as invalid input
                )
            total_seconds += current_value * time_units[char]
            current_value = 0  # Reset for next number-unit pair
        else:
            # Unknown character indicates an invalid format
            return 0

    return 0 if current_value != 0 else total_seconds


def seconds_to_human_readable(seconds: int) -> str:
    """
    Convert a number of seconds into a human readable string.

    Parameters
    ----------
    seconds : int
        The number of seconds to convert

    Returns
    -------
    str
        A string that breaks the time down by months, weeks, days, hours, minutes, and seconds.
    """
    units = (
        ("month", 2592000),
        ("week", 604800),
        ("day", 86400),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    )
    if seconds == 0:
        return "zero seconds"
    parts: list[str] = []
    for unit, div in units:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append(f"{amount} {unit}{'' if amount == 1 else 's'}")
    return ", ".join(parts)


def is_optional_param(param: commands.Parameter) -> bool:
    """
    Check if a parameter is optional.

    Parameters
    ----------
    param : commands.Parameter
        The parameter to check.

    Returns
    -------
    bool
        True if the parameter is optional, False otherwise.
    """
    if param.default is not inspect.Parameter.empty:
        return True

    param_type = param.annotation

    if get_origin(param_type) is Union:
        return type(None) in get_args(param_type)

    return False


def get_matching_string(arg: str) -> str:
    """
    Match the given argument to a specific string based on common usage.

    Parameters
    ----------
    arg : str
        The argument to match.

    Returns
    -------
    str
        The matching string, or None if no match is found.
    """
    match arg:
        case "user" | "target" | "member" | "username":
            return "@member"
        case "search_term":
            return "CIA"
        case "channel":
            return "#general"
        case "comic_id":
            return "1337"
        case _:
            return arg


def generate_usage(
    command: commands.Command[Any, Any, Any],
    flag_converter: type[commands.FlagConverter] | None = None,
) -> str:
    """
    Generate the usage string for a command.

    Parameters
    ----------
    command : commands.Command[Any, Any, Any]
        The command to generate the usage string for.
    flag_converter : type[commands.FlagConverter] | None
        The flag converter to use.

    Returns
    -------
    str
        The usage string for the command.
    """
    command_name = command.qualified_name
    usage = f"{command_name}"

    parameters: dict[str, commands.Parameter] = command.clean_params

    flag_prefix = getattr(flag_converter, "__commands_flag_prefix__", "-")
    flags: dict[str, commands.Flag] = (
        flag_converter.get_flags() if flag_converter else {}
    )

    # Handle regular parameters first
    for param_name, param in parameters.items():
        if param_name in {"ctx", "flags"}:
            continue

        is_required = not is_optional_param(param)
        matching_string = get_matching_string(param_name)

        if matching_string == param_name and is_required:
            matching_string = f"<{param_name}>"

        usage += f" {matching_string}" if is_required else f" [{matching_string}]"

    # Find positional flag if it exists
    positional_flag = None
    required_flags: list[str] = []
    optional_flags: list[str] = []

    for flag_name, flag_obj in flags.items():
        if getattr(flag_obj, "positional", False):
            positional_flag = flag_name
            continue

        flag = f"{flag_prefix}{flag_name}"

        if flag_obj.required:
            required_flags.append(flag)
        else:
            optional_flags.append(flag)

    # Add positional flag in its correct position
    if positional_flag:
        usage += f" [{positional_flag}]"

    # Add required flags
    for flag in required_flags:
        usage += f" {flag}"

    # Add optional flags
    if optional_flags:
        usage += f" [{' | '.join(optional_flags)}]"

    return usage


def docstring_parameter(*sub: Any) -> Any:
    """Parameterize docstrings with format-style substitution.

    Parameters
    ----------
    *sub : Any
        Substitution values to use in the docstring formatting.

    Returns
    -------
    Any
        The decorator function.
    """

    def dec(obj: Any) -> Any:
        """Apply parameter substitution to the object's docstring.

        Parameters
        ----------
        obj : Any
            The object whose docstring should be parameterized.

        Returns
        -------
        Any
            The object with modified docstring.
        """
        if obj.__doc__ is not None:
            obj.__doc__ = obj.__doc__.format(*sub)
        else:
            obj.__doc__ = "No docstring available. Substitution failed."
        return obj

    return dec
