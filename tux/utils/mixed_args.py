import re
from typing import Any

# Time pattern regex for detecting duration values - supports compound durations
time_regex = re.compile(r"^(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])+$")


def parse_mixed_arguments(argument_string: str) -> dict[str, Any]:
    """
    Parse mixed positional and flag arguments.

    This function can detect and parse both positional arguments and flag-based arguments
    from a single string, allowing commands to support multiple input formats.

    Parameters
    ----------
    argument_string : str
        The argument string to parse.

    Returns
    -------
    Dict[str, Any]
        A dictionary of parsed arguments with their values.

    Examples
    --------
    >>> parse_mixed_arguments("14d reason -s")
    {'duration': '14d', 'reason': 'reason', 'silent': True}

    >>> parse_mixed_arguments("reason -d 14d -s")
    {'reason': 'reason', 'duration': '14d', 'silent': True}
    """
    args = argument_string.split()
    result: dict[str, Any] = {}

    # Parse positional arguments first
    i = 0
    while i < len(args):
        arg = args[i]

        # Skip if it's already a flag
        if arg.startswith("-"):
            # Skip the flag and its value
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                i += 2  # Skip flag and its value
            else:
                i += 1  # Skip just the flag
            continue

        # Check if it matches time pattern (duration)
        if is_duration(arg):
            result["duration"] = arg
            i += 1
            continue

        # Check if it's a boolean-like value
        if arg.lower() in ("true", "false", "yes", "no", "1", "0"):
            result["silent"] = arg.lower() in ("true", "yes", "1")
            i += 1
            continue

        # Check if it's a number (could be purge days)
        if arg.isdigit() and 0 <= int(arg) <= 7:
            result["purge"] = int(arg)
            i += 1
            continue

        # If it's not a special pattern, treat as reason
        if "reason" not in result:
            result["reason"] = arg
        i += 1

    # Parse flag arguments - but don't override positional values
    i = 0
    while i < len(args):
        arg = args[i]

        if not arg.startswith("-"):
            i += 1
            continue

        # Remove the flag prefix
        flag_name = arg[1:].lower()

        # Get the flag value
        if i + 1 < len(args) and not args[i + 1].startswith("-"):
            value = args[i + 1]
            i += 2
        else:
            # Boolean flag or flag without value
            value = "true"
            i += 1

        # Convert the value based on flag type
        try:
            if flag_name in ("silent", "s", "quiet"):
                result["silent"] = value.lower() in ("true", "yes", "1")
            elif flag_name in ("duration", "d", "t", "time"):
                # Only set if not already set by positional
                if "duration" not in result:
                    result["duration"] = value
            elif flag_name in ("purge", "p"):
                result["purge"] = int(value)
            elif flag_name in ("reason", "r"):
                # Only set if not already set by positional
                if "reason" not in result:
                    result["reason"] = value
            else:
                result[flag_name] = value
        except (ValueError, TypeError):
            # Skip invalid values
            continue

    return result


def is_duration(text: str) -> bool:
    """
    Check if a string matches a duration pattern.

    Parameters
    ----------
    text : str
        The text to check.

    Returns
    -------
    bool
        True if the text matches a duration pattern.

    Examples
    --------
    >>> is_duration("14d")
    True
    >>> is_duration("1h30m")
    True
    >>> is_duration("reason")
    False
    """
    # Check for compound durations like "1h30m"
    if re.match(r"^(\d{1,5}(?:[.,]?\d{1,5})?[smhd])+$", text):
        return True

    # Check for simple durations
    return bool(time_regex.match(text))


def generate_mixed_usage(
    command_name: str,
    required_params: list[str],
    optional_params: list[str],
    flags: list[str],
) -> str:
    """
    Generate a usage string that shows both positional and flag formats.

    Parameters
    ----------
    command_name : str
        The name of the command.
    required_params : List[str]
        List of required parameters.
    optional_params : List[str]
        List of optional parameters.
    flags : List[str]
        List of available flags.

    Returns
    -------
    str
        A usage string showing both formats.

    Examples
    --------
    >>> generate_mixed_usage("timeout", ["member"], ["duration", "reason"], ["-d", "-s"])
    "timeout <member> [duration|reason] [-d] [-s]"
    """
    usage = command_name

    # Add required parameters
    for param in required_params:
        usage += f" <{param}>"

    # Add optional parameters
    if optional_params:
        usage += f" [{'|'.join(optional_params)}]"

    # Add flags
    if flags:
        # Format flags with individual brackets
        formatted_flags = [f"[{flag}]" for flag in flags]
        usage += f" {' '.join(formatted_flags)}"

    return usage


def extract_duration_from_args(args: list[str]) -> str | None:
    """
    Extract duration from a list of arguments.

    Parameters
    ----------
    args : List[str]
        List of arguments to search through.

    Returns
    -------
    Optional[str]
        The duration if found, None otherwise.
    """
    for arg in args:
        if is_duration(arg):
            return arg
    return None


def extract_reason_from_args(args: list[str]) -> str | None:
    """
    Extract reason from a list of arguments.

    Parameters
    ----------
    args : List[str]
        List of arguments to search through.

    Returns
    -------
    Optional[str]
        The reason if found, None otherwise.
    """
    for arg in args:
        if not arg.startswith("-") and not is_duration(arg) and not arg.isdigit():
            # Only return if it looks like a proper reason (not too generic)
            if len(arg) > 2 and arg.lower() not in ("other", "stuff", "things", "etc"):
                return arg
    return None
