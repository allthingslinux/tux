"""Error detail extraction utilities."""

import contextlib
from typing import Any


def unwrap_error(error: Any) -> Exception:
    """Unwrap nested exceptions to find root cause."""
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
    """Safely format error message with fallbacks."""
    # Try simple {error} formatting
    with contextlib.suppress(Exception):
        if "{error" in message_format:
            return message_format.format(error=error)

    # Return generic message
    return f"An unexpected error occurred. ({error!s})"


def format_list(items: list[str]) -> str:
    """Format list as comma-separated code blocks."""
    return ", ".join(f"`{item}`" for item in items)


def extract_missing_role_details(error: Exception) -> dict[str, Any]:
    """Extract missing role details."""
    role_id = getattr(error, "missing_role", None)
    if isinstance(role_id, int):
        return {"roles": f"<@&{role_id}>"}
    return {"roles": f"`{role_id}`" if role_id else "unknown role"}


def extract_missing_any_role_details(error: Exception) -> dict[str, Any]:
    """Extract missing roles list."""
    roles_list = getattr(error, "missing_roles", [])
    formatted_roles: list[str] = []

    for role in roles_list:
        if isinstance(role, int):
            formatted_roles.append(f"<@&{role}>")
        else:
            formatted_roles.append(f"`{role}`")

    return {"roles": ", ".join(formatted_roles) if formatted_roles else "unknown roles"}


def extract_permissions_details(error: Exception) -> dict[str, Any]:
    """Extract missing permissions."""
    perms = getattr(error, "missing_perms", [])
    return {"permissions": format_list(perms)}


def extract_bad_flag_argument_details(error: Exception) -> dict[str, Any]:
    """Extract flag argument details."""
    flag_name = getattr(getattr(error, "flag", None), "name", "unknown_flag")
    original_cause = getattr(error, "original", error)
    return {"flag_name": flag_name, "original_cause": original_cause}


def extract_missing_flag_details(error: Exception) -> dict[str, Any]:
    """Extract missing flag details."""
    flag_name = getattr(getattr(error, "flag", None), "name", "unknown_flag")
    return {"flag_name": flag_name}


def extract_httpx_status_details(error: Exception) -> dict[str, Any]:
    """Extract HTTPX status error details."""
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


def extract_missing_argument_details(error: Exception) -> dict[str, Any]:
    """Extract missing argument details."""
    param_name = getattr(getattr(error, "param", None), "name", "unknown_argument")
    return {"param_name": param_name}
