import re
from collections.abc import Callable
from typing import Any

from discord.ext import commands

# Time pattern regex for detecting duration values
time_regex = re.compile(r"^(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])$")


def flexible_command(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Any]:
    """
    A decorator that allows commands to accept both positional and flag arguments.

    This allows commands to accept arguments in multiple formats:
    - Traditional flags: `command @user reason -d 14d`
    - Positional arguments: `command @user 14d reason`
    - Mixed usage: `command @user 14d reason -s`

    Positional arguments take precedence over flag arguments when both are provided.
    """

    def decorator(func: Callable[..., Any]) -> Any:
        # Create a wrapper that handles mixed argument parsing
        async def wrapper(self: Any, ctx: commands.Context[Any], *args: Any, **kwargs: Any) -> Any:
            # Get the original command arguments
            if args:
                # Parse mixed arguments
                parsed_args = parse_mixed_arguments(args[0] if isinstance(args[0], str) else " ".join(args))

                # Update kwargs with parsed values
                kwargs.update(parsed_args)

            # Call the original function
            return await func(self, ctx, *args, **kwargs)

        # Apply the original command decorator
        return commands.hybrid_command(*args, **kwargs)(wrapper)

    return decorator


def parse_mixed_arguments(argument_string: str) -> dict[str, Any]:
    """
    Parse mixed positional and flag arguments.

    Parameters
    ----------
    argument_string : str
        The argument string to parse.

    Returns
    -------
    Dict[str, Any]
        A dictionary of parsed arguments.
    """
    args = argument_string.split()
    result: dict[str, Any] = {}

    # Parse positional arguments first
    for arg in args:
        # Skip if it's already a flag
        if arg.startswith("-"):
            continue

        # Check if it matches time pattern (duration)
        if time_regex.match(arg):
            result["duration"] = arg
            continue

        # Check if it's a boolean-like value
        if arg.lower() in ("true", "false", "yes", "no", "1", "0"):
            result["silent"] = arg.lower() in ("true", "yes", "1")
            continue

        # Check if it's a number (could be purge days)
        if arg.isdigit() and 0 <= int(arg) <= 7:
            result["purge"] = int(arg)
            continue

    # Parse flag arguments
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
                result["duration"] = value
            elif flag_name in ("purge", "p"):
                result["purge"] = int(value)
            else:
                result[flag_name] = value
        except (ValueError, TypeError):
            # Skip invalid values
            continue

    return result


def detect_time_argument(arg: str) -> bool:
    """
    Detect if an argument is a time-based value.

    Parameters
    ----------
    arg : str
        The argument to check.

    Returns
    -------
    bool
        True if the argument matches a time pattern.
    """
    return bool(time_regex.match(arg))


def generate_flexible_usage(
    command: commands.Command[Any, Any, Any],
    flag_converter: type[commands.FlagConverter] | None = None,
) -> str:
    """
    Generate a flexible usage string that shows both positional and flag formats.

    Parameters
    ----------
    command : commands.Command[Any, Any, Any]
        The command to generate the usage string for.
    flag_converter : type[commands.FlagConverter] | None
        The flag converter to use.

    Returns
    -------
    str
        The flexible usage string for the command.
    """
    command_name = command.qualified_name
    usage = f"{command_name}"

    parameters: dict[str, commands.Parameter] = command.clean_params
    flags: dict[str, commands.Flag] = flag_converter.get_flags() if flag_converter else {}

    # Handle regular parameters first
    for param_name, param in parameters.items():
        if param_name in {"ctx", "flags"}:
            continue

        is_required = not _is_optional_param(param)
        matching_string = _get_matching_string(param_name)

        if matching_string == param_name and is_required:
            matching_string = f"<{param_name}>"

        usage += f" {matching_string}" if is_required else f" [{matching_string}]"

    # Build flexible flag usage
    positional_flags: list[str] = []
    required_flags: list[str] = []
    optional_flags: list[str] = []

    for flag_name, flag_obj in flags.items():
        if getattr(flag_obj, "positional", False):
            # This is already handled as a positional argument
            continue

        # Check if this flag could be positional
        if _can_be_positional(flag_name, flag_obj):
            positional_flags.append(f"[{flag_name}]")

        # Add to appropriate flag list
        flag = f"-{flag_name}"
        if flag_obj.required:
            required_flags.append(flag)
        else:
            optional_flags.append(flag)

    # Add positional flags
    if positional_flags:
        usage += f" {' '.join(positional_flags)}"

    # Add required flags
    for flag in required_flags:
        usage += f" {flag}"

    # Add optional flags
    if optional_flags:
        usage += f" [{' | '.join(optional_flags)}]"

    return usage


def _can_be_positional(flag_name: str, flag_obj: commands.Flag) -> bool:
    """
    Determine if a flag can be used as a positional argument.

    Parameters
    ----------
    flag_name : str
        The name of the flag.
    flag_obj : commands.Flag
        The flag object.

    Returns
    -------
    bool
        True if the flag can be used positionally.
    """
    # Duration flags can be positional
    if flag_name in ("duration", "time", "d", "t"):
        return True

    # Boolean flags are typically better as explicit flags
    if flag_obj.annotation == bool:
        return False

    # Numeric flags with limited ranges can be positional
    if hasattr(flag_obj, "min_value") and hasattr(flag_obj, "max_value"):
        return True

    return False


def _is_optional_param(param: commands.Parameter) -> bool:
    """Check if a parameter is optional."""
    return param.default is not param.empty or param.required is False


def _get_matching_string(arg: str) -> str:
    """Get a matching string for an argument."""
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
