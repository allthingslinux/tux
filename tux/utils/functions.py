import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import discord

harmful_command_pattern = r"(?:sudo\s+|doas\s+|run0\s+)?rm\s+(-[frR]*|--force|--recursive|--no-preserve-root|\s+)*(/\s*|\*|/bin|/boot|/etc|/lib|/proc|/root|/sbin|/sys|/tmp|/usr|/var|/var/log|/network.|/system)(\s+--no-preserve-root|\s+\*)*|:\(\)\{ :|:& \};:"


def is_harmful(command: str) -> bool:
    first_test: bool = re.search(harmful_command_pattern, command) is not None
    second_test: bool = re.search(r"rm.{0,5}[rfRF]", command) is not None
    return first_test and second_test


def strip_formatting(content: str) -> str:
    # Remove triple backtick blocks considering any spaces and platform-specific newlines
    content = re.sub(r"`/```(.*)```/", "", content, flags=re.DOTALL)
    # Remove inline code snippets preserving their content only
    content = re.sub(r"`([^`]*)`", r"\1", content)
    # Remove Markdown headers
    content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)
    # Remove other common markdown symbols
    content = re.sub(r"[\*_~|>]", "", content)

    return content.strip()


def convert_to_seconds(time_str: str) -> int:
    """
    Converts a formatted time string with the formats Mwdhms
    Any unexpected format leads to returning 0.

    Parameters:
    ----------
    time_str : str
        The formatted time string to convert to total seconds.

    Returns:
    -------
    int
        The total seconds from the formatted time string.
    """

    # Time conversion factors from units to seconds
    time_units = {
        "M": 2592000,  # Months to seconds
        "w": 604800,  # Weeks to seconds
        "d": 86400,  # Days to seconds
        "h": 3600,  # Hours to seconds
        "m": 60,  # Minutes to seconds
        "s": 1,  # Seconds to seconds
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
                return 0  # No number specified for the unit, thus treat as invalid input
            total_seconds += current_value * time_units[char]
            current_value = 0  # Reset for next number-unit pair
        else:
            # Unknown character indicates an invalid format
            return 0

    return 0 if current_value != 0 else total_seconds


def datetime_to_unix(dt: datetime | None):
    """
    This function accepts a datetime object or None, converts it into a Unix timestamp
    and returns it as a formatted Discord timestamp string or 'Never'

    Parameters:
    ----------
    dt : datetime
        The datetime object to convert to a Discord timestamp string.

    Returns:
    -------
    str
        The formatted Discord timestamp string or 'Never'
    """

    if dt is None:
        return "Never"

    unix_timestamp = int(dt.timestamp())

    return f"<t:{unix_timestamp}>"


def datetime_to_elapsed_time(dt: datetime | None):
    """
    Takes a datetime and computes the elapsed time from then to now in the format: X years, Y months, Z days.

    Parameters:
    ----------
    dt : datetime
        The datetime object to compute the elapsed time from.

    Returns:
    -------
    str
        The elapsed time in the format: X years, Y months, Z days.
    """

    if dt is None:
        return "Never"

    elapsed_time = datetime.now(UTC) - dt
    elapsed_days = elapsed_time.days

    years, days_left = divmod(elapsed_days, 365)
    months, days_left = divmod(days_left, 30)

    return f"{years} years, {months} months, {days_left} days"


def compare_changes(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    """
    Compares the changes between two dictionaries and returns a list of strings representing the changes.

    Parameters:
    ----------
    before : dict
        The dictionary representing the state before the changes.
    after : dict
        The dictionary representing the state after the changes.

    Returns:
    -------
    list
        A list of strings showing the changes made in the dictionaries.
    """

    return [f"{key}: {before[key]} -> {after[key]}" for key in before if key in after and before[key] != after[key]]


def compare_guild_channel_changes(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel) -> list[str]:
    """
    Compares the changes between two GuildChannel instances and returns a list of strings representing the changes.

    Parameters:
    ----------
    before : discord.abc.GuildChannel
        The GuildChannel instance representing the state before the changes.
    after : discord.abc.GuildChannel
        The GuildChannel instance representing the state after the changes.

    Returns:
    -------
    list
        A list of strings showing the changes made in the GuildChannel instances.
    """

    keys = [
        "category",
        "changed_roles",
        "created_at",
        "guild",
        "name",
        "overwrites",
        "permissions_synced",
        "position",
    ]

    return [
        f"{key}: {getattr(before, key)} -> {getattr(after, key)}"
        for key in keys
        if getattr(before, key) != getattr(after, key)
    ]


def compare_member_changes(before: discord.Member | discord.User, after: discord.Member | discord.User) -> list[str]:
    """
    Compares changes between two Member instances and returns a list of strings representing the changes.

    Parameters:
    ----------
    before : discord.Member
        The Member instance representing the state before the changes.
    after : discord.Member
        The Member instance representing the state after the changes.

    Returns:
    -------
    list
        A list of strings showing the changes made in the Member instances.
    """

    keys = ["name", "display_name", "global_name"]

    return [
        f"{key}: {getattr(before, key)} -> {getattr(after, key)}"
        for key in keys
        if getattr(before, key) != getattr(after, key)
    ]


def extract_guild_attrs(guild: discord.Guild) -> dict[str, Any]:
    """
    Extracts relevant attributes from a discord.Guild and returns them as a dictionary.

    Parameters:
    ----------
    guild : discord.Guild
        The discord.Guild instance to extract attributes from.

    Returns:
    -------
    dict
        A dictionary containing the extracted attributes of the guild.
    """

    return {
        "name": guild.name,
        "description": guild.description,
        "member_count": guild.member_count,
        "verification_level": str(guild.verification_level),
        "system_channel": guild.system_channel,
    }


def extract_member_attrs(member: discord.Member) -> dict[str, Any]:
    """
    Extracts relevant attributes from a discord.Member and returns them as a dictionary.

    Parameters:
    ----------
    member : discord.Member
        The discord.Member instance to extract attributes from.

    Returns:
    -------
    dict
        A dictionary containing the extracted attributes of the member.
    """

    return {
        "name": member.name,
        "nick": member.nick,
        "roles": member.roles,
        "joined_at": member.joined_at,
        "status": member.status,
        "activity": member.activity,
    }


def get_local_time() -> datetime:
    """
    Get the current local time.

    Returns:
    -------
    datetime
        The current local time.
    """

    local_timezone = datetime.now(UTC).astimezone().tzinfo
    return datetime.now(local_timezone)


def days(day: str | int) -> str:
    """
    Returns the number of days ago in a human-readable format.

    Parameters:
    ----------
    day : str | int
        The number of days ago.

    Returns:
    -------
    str
        The number of days ago in a human-readable format.
    """

    day = int(day)

    if day == 0:
        return "**today**"

    return f"{day} day ago" if day == 1 else f"{day} days ago"


def truncate(text: str, max_len: int = 1024) -> str:
    """
    Truncates a string to a specified length.

    Parameters:
    ----------
    text : str
        The string to truncate.
    max_len : int
        The maximum length of the truncated string.

    Returns:
    -------
    str
        The truncated string.
    """

    etc = "\n[…]"

    return f"{text[:max_len - len(etc)]}{etc}" if len(text) > max_len - len(etc) else text


def ordinal(n: int) -> str:
    """
    Returns the ordinal representation of a number.

    Parameters:
    ----------
    n : int
        The number to convert to an ordinal.

    Returns:
    -------
    str
        The ordinal representation of the number.
    """

    return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")


def is_convertible_to_type(string: str, type_func: Callable[..., object]) -> bool:
    """
    Checks if a string is convertible to a specified type.

    Parameters:
    ----------
    string : str
        The string to check.
    type_func : Callable
        The function to convert the string to a specified type.

    Returns:
    -------
    bool
        True if the string is convertible to the specified type, False otherwise.

    Raises:
    -------
    ValueError
        If the string is not convertible to the specified type.
    """

    try:
        type_func(string)
    except ValueError:
        return False
    else:
        return True


def is_integer(string: str):
    """
    Checks if a string is convertible to an integer.

    Parameters:
    ----------
    string : str
        The string to check.

    Returns:
    -------
    bool
        True if the string is convertible to an integer, False otherwise.
    """

    return is_convertible_to_type(string, int)


def is_float(string: str):
    """
    Checks if a string is convertible to a float.

    Parameters:
    ----------
    string : str
        The string to check.

    Returns:
    -------
    bool
        True if the string is convertible to a float, False otherwise.
    """

    return is_convertible_to_type(string, float)
