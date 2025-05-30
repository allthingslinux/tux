import re
from datetime import UTC, datetime, timedelta
from typing import Any

import discord

DANGEROUS_RM_COMMANDS = (
    # Privilege escalation prefixes
    r"(?:sudo\s+|doas\s+|run0\s+)?"
    # rm command
    r"rm\s+"
    # rm options
    r"(?:-[frR]+|--force|--recursive|--no-preserve-root|\s+)*"
    # Root/home indicators
    r"(?:[/\∕~]\s*|\*|"  # noqa: RUF001
    # Critical system paths
    r"/(?:bin|boot|etc|lib|proc|root|sbin|sys|tmp|usr|var(?:/log)?|network\.|system))"
    # Additional dangerous flags
    r"(?:\s+--no-preserve-root|\s+\*)*"
)

FORK_BOMB_PATTERNS = [":(){:&};:", ":(){:|:&};:"]

DANGEROUS_DD_COMMANDS = r"dd\s+.*of=/dev/([hs]d[a-z]|nvme\d+n\d+)"

FORMAT_COMMANDS = r"mkfs\..*\s+/dev/([hs]d[a-z]|nvme\d+n\d+)"


def truncate(text: str, length: int) -> str:
    """Truncates a string to a specified length.

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


def is_harmful(command: str) -> str | None:
    # sourcery skip: assign-if-exp, boolean-if-exp-identity, reintroduce-else
    """
    Check if a command is potentially harmful to the system.

    Parameters
    ----------
    command : str
        The command to check.

    Returns
    -------
    bool
        True if the command is harmful, False otherwise.
    """
    # Normalize command by removing all whitespace for fork bomb check
    normalized = "".join(command.strip().lower().split())
    if normalized in FORK_BOMB_PATTERNS:
        return "FORK_BOMB"

    # Check for dangerous rm commands
    if re.search(DANGEROUS_RM_COMMANDS, command, re.IGNORECASE):
        return "RM_COMMAND"

    # Check for dangerous dd commands
    if re.search(DANGEROUS_DD_COMMANDS, command, re.IGNORECASE):
        return "DD_COMMAND"

    # Check for format commands
    if bool(re.search(FORMAT_COMMANDS, command, re.IGNORECASE)):
        return "FORMAT_COMMAND"
    return None


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
    Converts a formatted time string with the formats Mwdhms
    Any unexpected format leads to returning 0.

    Parameters
    ----------
    time_str : str
        The formatted time string to convert to total seconds.

    Returns
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


def seconds_to_human_readable(seconds: int) -> str:
    """
    Converts a number of seconds into a human readable string

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


def datetime_to_unix(dt: datetime | None) -> str:
    """
    This function accepts a datetime object or None, converts it into a Unix timestamp
    and returns it as a formatted Discord timestamp string or 'Never'

    Parameters
    ----------
    dt : datetime
        The datetime object to convert to a Discord timestamp string.

    Returns
    -------
    str
        The formatted Discord timestamp string or 'Never'
    """

    if dt is None:
        return "Never"

    unix_timestamp = int(dt.timestamp())

    return f"<t:{unix_timestamp}>"


def datetime_to_elapsed_time(dt: datetime | None) -> str:
    """
    Takes a datetime and computes the elapsed time from then to now in the format: X years, Y months, Z days.

    Parameters
    ----------
    dt : datetime
        The datetime object to compute the elapsed time from.

    Returns
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

    Parameters
    ----------
    before : dict
        The dictionary representing the state before the changes.
    after : dict
        The dictionary representing the state after the changes.

    Returns
    -------
    list
        A list of strings showing the changes made in the dictionaries.
    """

    return [f"{key}: {before[key]} -> {after[key]}" for key in before if key in after and before[key] != after[key]]


def compare_guild_channel_changes(
    before: discord.abc.GuildChannel,
    after: discord.abc.GuildChannel,
) -> list[str]:
    """
    Compares the changes between two GuildChannel instances and returns a list of strings representing the changes.

    Parameters
    ----------
    before : discord.abc.GuildChannel
        The GuildChannel instance representing the state before the changes.
    after : discord.abc.GuildChannel
        The GuildChannel instance representing the state after the changes.

    Returns
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


def compare_member_changes(
    before: discord.Member | discord.User,
    after: discord.Member | discord.User,
) -> list[str]:
    """
    Compares changes between two Member instances and returns a list of strings representing the changes.

    Parameters
    ----------
    before : discord.Member
        The Member instance representing the state before the changes.
    after : discord.Member
        The Member instance representing the state after the changes.

    Returns
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

    Parameters
    ----------
    guild : discord.Guild
        The discord.Guild instance to extract attributes from.

    Returns
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
    """Extract relevant attributes from a member object.

    Parameters
    ----------
    member : discord.Member
        The member object to extract attributes from.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the extracted attributes.
    """
    return {
        "name": member.name,
        "id": member.id,
        "discriminator": member.discriminator,
        "display_name": member.display_name,
        "roles": [role.name for role in member.roles],
        "joined_at": member.joined_at,
        "status": str(member.status),
        "activity": str(member.activity) if member.activity else None,
    }


def docstring_parameter(*sub: Any) -> Any:
    def dec(obj: Any) -> Any:
        if obj.__doc__ is not None:
            obj.__doc__ = obj.__doc__.format(*sub)
        else:
            obj.__doc__ = "No docstring available. Substitution failed."
        return obj

    return dec
