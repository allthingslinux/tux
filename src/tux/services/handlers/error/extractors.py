"""Error detail extraction utilities."""

import contextlib
from typing import Any

from tux.services.handlers.error.config import DEFAULT_ERROR_MESSAGE


def unwrap_error(error: Any) -> Exception:
    """
    Unwrap nested exceptions to find root cause.

    Returns
    -------
    Exception
        The unwrapped root exception.
    """
    current = error
    loops = 0
    max_loops = 10

    while hasattr(current, "original") and loops < max_loops:
        next_error = current.original
        if next_error is current:
            break
        current = next_error
        loops += 1

    if not isinstance(current, Exception):
        return ValueError(f"Non-exception after unwrapping: {current!r}")

    return current


def fallback_format_message(message_format: str, error: Exception) -> str:
    """
    Safely format error message with fallbacks.

    Returns
    -------
    str
        The formatted error message.
    """
    # Try simple {error} formatting
    with contextlib.suppress(Exception):
        if "{error" in message_format:
            return message_format.format(error=error)

    # Return the default error message when formatting fails
    return DEFAULT_ERROR_MESSAGE


def format_list(items: list[str]) -> str:
    """
    Format list as comma-separated code blocks.

    Returns
    -------
    str
        Comma-separated list in code blocks.
    """
    return ", ".join(f"`{item}`" for item in items)


def extract_missing_role_details(error: Exception, **_kwargs: Any) -> dict[str, Any]:
    """
    Extract missing role details.

    Parameters
    ----------
    error : Exception
        The missing role error.
    **_kwargs : Any
        Additional context (unused but part of extractor interface).

    Returns
    -------
    dict[str, Any]
        Dictionary containing role information.
    """
    role_id = getattr(error, "missing_role", None)
    if isinstance(role_id, int):
        return {"roles": f"<@&{role_id}>"}
    return {"roles": f"`{role_id}`" if role_id else "unknown role"}


def extract_missing_any_role_details(
    error: Exception,
    **_kwargs: Any,
) -> dict[str, Any]:
    """
    Extract missing roles list.

    Parameters
    ----------
    error : Exception
        The missing any role error.
    **_kwargs : Any
        Additional context (unused but part of extractor interface).

    Returns
    -------
    dict[str, Any]
        Dictionary containing roles information.
    """
    roles_list = getattr(error, "missing_roles", [])
    formatted_roles: list[str] = []

    for role in roles_list:
        if isinstance(role, int):
            formatted_roles.append(f"<@&{role}>")
        else:
            formatted_roles.append(f"`{role}`")

    return {"roles": ", ".join(formatted_roles) if formatted_roles else "unknown roles"}


def extract_permissions_details(error: Exception, **_kwargs: Any) -> dict[str, Any]:
    """
    Extract missing permissions.

    Parameters
    ----------
    error : Exception
        The missing permissions error.
    **_kwargs : Any
        Additional context (unused but part of extractor interface).

    Returns
    -------
    dict[str, Any]
        Dictionary containing permissions information.
    """
    perms = getattr(error, "missing_perms", [])
    return {"permissions": format_list(perms)}


def extract_bad_flag_argument_details(
    error: Exception,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Extract flag argument details.

    Parameters
    ----------
    error : Exception
        The bad flag argument error.
    **kwargs : Any
        Additional context, may include 'source' for command information.

    Returns
    -------
    dict[str, Any]
        Dictionary containing flag details, original cause, and usage information.
    """
    flag_name = getattr(getattr(error, "flag", None), "name", "unknown_flag")
    original_cause = getattr(error, "original", error)

    result = {"flag_name": flag_name, "original_cause": original_cause}

    # Try to get command usage if available
    usage_str = ""
    source = kwargs.get("source")
    if source:
        with contextlib.suppress(Exception):
            # For traditional commands
            if (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "usage")
                and source.command.usage
            ):
                usage_str = f"\nUsage: `{source.command.usage}`"
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "signature")
                and source.command.signature
            ):
                usage_str = f"\nUsage: `{source.command.qualified_name} {source.command.signature}`"

            # For slash commands
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "qualified_name")
            ):
                usage_str = f"\nUsage: `/{source.command.qualified_name}`"

    result["usage"] = usage_str
    return result


def extract_missing_flag_details(error: Exception, **kwargs: Any) -> dict[str, Any]:
    """
    Extract missing flag details.

    Parameters
    ----------
    error : Exception
        The missing flag error.
    **kwargs : Any
        Additional context, may include 'source' for command information.

    Returns
    -------
    dict[str, Any]
        Dictionary containing flag name and usage information.
    """
    flag_name = getattr(getattr(error, "flag", None), "name", "unknown_flag")

    result = {"flag_name": flag_name}

    # Try to get command usage if available
    usage_str = ""
    source = kwargs.get("source")
    if source:
        with contextlib.suppress(Exception):
            # For traditional commands
            if (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "usage")
                and source.command.usage
            ):
                usage_str = f"\nUsage: `{source.command.usage}`"
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "signature")
                and source.command.signature
            ):
                usage_str = f"\nUsage: `{source.command.qualified_name} {source.command.signature}`"

            # For slash commands
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "qualified_name")
            ):
                usage_str = f"\nUsage: `/{source.command.qualified_name}`"

    result["usage"] = usage_str
    return result


def extract_httpx_status_details(error: Exception, **_kwargs: Any) -> dict[str, Any]:
    """
    Extract HTTPX status error details.

    Parameters
    ----------
    error : Exception
        The HTTPX status error.
    **_kwargs : Any
        Additional context (unused but part of extractor interface).

    Returns
    -------
    dict[str, Any]
        Dictionary containing status code, URL, and response text.
    """
    try:
        if not hasattr(error, "response"):
            return {}

        response = getattr(error, "response", None)
        if response is None:
            return {}

        status_code = getattr(response, "status_code", "unknown")
        text = getattr(response, "text", "no response text")
        url = getattr(response, "url", "unknown")

        return {
            "status_code": status_code,
            "response_text": str(text)[:200],
            "url": str(url),
        }
    except (AttributeError, TypeError):
        return {}


def extract_missing_argument_details(error: Exception, **kwargs: Any) -> dict[str, Any]:
    """
    Extract missing argument details.

    Parameters
    ----------
    error : Exception
        The missing argument error.
    **kwargs : Any
        Additional context, may include 'source' for command information.

    Returns
    -------
    dict[str, Any]
        Dictionary containing parameter name and usage information.
    """
    param_name = getattr(getattr(error, "param", None), "name", "unknown_argument")

    result = {"param_name": param_name}

    # Try to get command usage if available
    usage_str = ""
    source = kwargs.get("source")
    if source:
        with contextlib.suppress(Exception):
            # For traditional commands
            if (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "usage")
                and source.command.usage
            ):
                usage_str = f"\nUsage: `{source.command.usage}`"
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "signature")
                and source.command.signature
            ):
                usage_str = f"\nUsage: `{source.command.qualified_name} {source.command.signature}`"

            # For slash commands
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "qualified_name")
            ):
                usage_str = f"\nUsage: `/{source.command.qualified_name}`"

    result["usage"] = usage_str
    return result


def extract_bad_union_argument_details(
    error: Exception,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Extract bad union argument details.

    Parameters
    ----------
    error : Exception
        The bad union argument error.
    **kwargs : Any
        Additional context, may include 'source' for command information.

    Returns
    -------
    dict[str, Any]
        Dictionary containing argument, expected types, and usage information.
    """
    # Try to extract the actual argument value
    argument_raw = getattr(error, "argument", getattr(error, "param", "unknown"))

    # If argument_raw is a Parameter object, get its name
    if hasattr(argument_raw, "name"):
        argument = getattr(argument_raw, "name", "unknown")
    elif isinstance(argument_raw, str):
        # Parse string format like "member: Union[...]"
        argument = argument_raw.split(": ")[0] if ": " in argument_raw else argument_raw
    else:
        argument = str(argument_raw) if argument_raw is not None else "unknown"

    converters = getattr(error, "converters", [])

    # Format the expected types
    expected_types: list[str] = []
    for converter in converters:
        try:
            if hasattr(converter, "__name__"):
                expected_types.append(str(converter.__name__))
            elif hasattr(converter, "_type"):
                # Accessing discord.py internal _type attribute for error messages
                expected_types.append(str(converter._type))
            else:
                expected_types.append(str(converter))
        except Exception:
            # str() conversion can fail for various converter types (AttributeError, TypeError, etc.)
            # Catching Exception is appropriate here as we want to continue with "unknown" fallback
            expected_types.append("unknown")

    expected_types_str = (
        " or ".join(expected_types) if expected_types else "unknown type"
    )

    result = {"argument": argument, "expected_types": expected_types_str}

    # Try to get command usage if available
    usage_str = ""
    source = kwargs.get("source")
    if source:
        with contextlib.suppress(Exception):
            # For traditional commands
            if (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "usage")
                and source.command.usage
            ):
                usage_str = f"\nUsage: `{source.command.usage}`"
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "signature")
                and source.command.signature
            ):
                usage_str = f"\nUsage: `{source.command.qualified_name} {source.command.signature}`"

            # For slash commands
            elif (
                hasattr(source, "command")
                and source.command
                and hasattr(source.command, "qualified_name")
            ):
                usage_str = f"\nUsage: `/{source.command.qualified_name}`"

    result["usage"] = usage_str
    return result


def extract_permission_denied_details(
    error: Exception,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Extract permission denied error details.

    Parameters
    ----------
    error : Exception
        The permission denied error.
    **kwargs : Any
        Additional context, may include 'ctx' for command context.

    Returns
    -------
    dict[str, Any]
        Dictionary containing formatted permission message.
    """
    required_rank = getattr(error, "required_rank", 0)
    user_rank = getattr(error, "user_rank", 0)
    command_name = getattr(error, "command_name", "this command")

    # Check if this is an unconfigured command error (both ranks are 0)
    if required_rank == 0 and user_rank == 0:
        # Try to get prefix from context (check cache synchronously)
        prefix = "$"  # Default fallback
        ctx = kwargs.get("ctx")
        if (
            ctx
            and hasattr(ctx, "bot")
            and hasattr(ctx.bot, "prefix_manager")
            and ctx.guild
        ):
            with contextlib.suppress(Exception):
                # Access the cache directly (synchronous) - accessing private member for performance
                prefix_manager = ctx.bot.prefix_manager
                if ctx.guild.id in prefix_manager._prefix_cache:
                    prefix = prefix_manager._prefix_cache[ctx.guild.id]

        message = (
            f"**`{command_name}`** has not been configured yet.\n\n"
            f"An administrator must assign a permission rank to enable this command.\n\n"
            f"Use `/config overview` or `{prefix}config overview` to configure command permissions."
        )
    else:
        message = f"You need permission rank **{required_rank}** to use **`{command_name}`**.\n\nYour current rank: **{user_rank}**"

    return {"message": message}
