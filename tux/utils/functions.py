import inspect
import re
from datetime import timedelta
from typing import Any, Union, get_args, get_origin

from discord.ext import commands

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
    Matches the given argument to a specific string based on common usage.

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
    flags: dict[str, commands.Flag] = flag_converter.get_flags() if flag_converter else {}

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
    def dec(obj: Any) -> Any:
        if obj.__doc__ is not None:
            obj.__doc__ = obj.__doc__.format(*sub)
        else:
            obj.__doc__ = "No docstring available. Substitution failed."
        return obj

    return dec
