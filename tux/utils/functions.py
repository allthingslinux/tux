from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import discord


def compare_changes(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    """
    Compares the changes between two dictionaries and returns a list of strings representing the changes.

    Args:
        before: The dictionary representing the state before the changes.
        after: The dictionary representing the state after the changes.

    Returns:
        A list of strings showing the changes made in the dictionaries.
    """

    return [
        f"{key}: {before[key]} -> {after[key]}"
        for key in before
        if key in after and before[key] != after[key]
    ]


def extract_guild_attrs(guild: discord.Guild) -> dict[str, Any]:
    """
    Extracts relevant attributes from a discord.Guild and returns them as a dictionary.

    Args:
        guild: The discord.Guild instance to extract attributes from.

    Returns:
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

    Args:
        member: The discord.Member instance to extract attributes from.

    Returns:
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
    """Returns the current local time.

    Returns:
        Offset aware datetime object.
    """
    local_timezone = datetime.now(UTC).astimezone().tzinfo
    return datetime.now(local_timezone)


def days(day: str | int) -> str:
    """Humanize the number of days.

    Args:
      day: Union[int, str]
          The number of days passed.

    Returns:
      str
          A formatted string of the number of days passed.
    """
    day = int(day)
    if day == 0:
        return "**today**"
    return f"{day} day ago" if day == 1 else f"{day} days ago"


def truncate(text: str, max_len: int = 1024) -> str:
    """Truncate a paragraph to a specific length.

    Args:
        text: The paragraph to truncate.
        max_len: The maximum length of the paragraph.

    Returns:
        The truncated paragraph.
    """
    etc = "\n[…]"
    return f"{text[:max_len - len(etc)]}{etc}" if len(text) > max_len - len(etc) else text


def ordinal(n: int) -> str:
    """Return number with ordinal suffix eg. 1st, 2nd, 3rd, 4th..."""
    return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")


def is_convertible_to_type(string: str, type_func: Callable[..., object]) -> bool:
    """Checks if the string can be converted to a specific type

    Args:
        string (str): The string to check
        type_func (callable): The function to use for conversion

    Returns:
        Boolean: Whether the string could be converted to the specified type or not
    """
    try:
        type_func(string)
    except ValueError:
        return False
    else:
        return True


def is_integer(string: str):
    return is_convertible_to_type(string, int)


def is_float(string: str):
    return is_convertible_to_type(string, float)
