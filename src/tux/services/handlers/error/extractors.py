"""Error detail extraction utilities."""

from typing import Any


def format_list(items: list[str]) -> str:
    """Format a list of items into a human-readable string."""
    return ", ".join(f"`{item}`" for item in items)


def unwrap_error(error: Any) -> Exception:
    """
    Recursively unwraps nested exceptions to find the root cause.

    This function traverses through exception chains (like CommandInvokeError
    wrapping other exceptions) to find the underlying error that actually
    occurred. This is crucial for proper error classification and user-friendly
    error messages.

    Args:
        error: The exception to unwrap, which may be nested.

    Returns:
        The root exception after unwrapping all nested layers.

    Example:
        If we have CommandInvokeError(original=ValueError("Invalid input")),
        this function will return the ValueError instance.
    """
    current_error = error

    # Keep unwrapping while we have nested exceptions
    while hasattr(current_error, "original") and current_error.original is not None:
        current_error = current_error.original

    return current_error


def fallback_format_message(message_format: str, error: Exception) -> str:
    """
    Safely formats an error message with fallback handling.

    This function attempts to format a message template with error details,
    but gracefully handles cases where the formatting might fail (e.g., due
    to missing attributes or unexpected error types).

    Args:
        message_format: The message template string to format.
        error: The exception to extract information from.

    Returns:
        The formatted message, or a safe fallback if formatting fails.
    """
    try:
        return message_format.format(error=error)
    except (AttributeError, KeyError, ValueError):
        # If formatting fails for any reason, return a generic message
        # This prevents the error handler itself from crashing
        return f"An error occurred: {type(error).__name__}"


def extract_missing_role_details(error: Exception) -> dict[str, Any]:
    """Extract details from MissingRole error."""
    return {
        "missing_role": getattr(error, "missing_role", "Unknown role"),
    }


def extract_missing_any_role_details(error: Exception) -> dict[str, Any]:
    """Extract details from MissingAnyRole error."""
    missing_roles = getattr(error, "missing_roles", [])
    return {
        "missing_roles": format_list([str(role) for role in missing_roles]) if missing_roles else "Unknown roles",
    }


def extract_permissions_details(error: Exception) -> dict[str, Any]:
    """Extract details from permission-related errors."""
    missing_permissions = getattr(error, "missing_permissions", [])
    return {"missing_permissions": format_list(missing_permissions) if missing_permissions else "Unknown permissions"}


def extract_bad_flag_argument_details(error: Exception) -> dict[str, Any]:
    """Extract details from BadFlagArgument error."""
    return {
        "flag_name": getattr(error, "flag", "Unknown flag"),
    }


def extract_missing_flag_details(error: Exception) -> dict[str, Any]:
    """Extract details from MissingFlagArgument error."""
    return {
        "flag_name": getattr(error, "flag", "Unknown flag"),
    }


def extract_missing_argument_details(error: Exception) -> dict[str, Any]:
    """Extract details from MissingRequiredArgument error."""
    return {
        "param_name": getattr(error, "param", "Unknown parameter"),
    }
