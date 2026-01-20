"""
Utility functions for database migration.

Provides helper functions for name conversion, type transformation,
and data validation during migration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast

from loguru import logger


def convert_prisma_to_sqlmodel_name(prisma_name: str) -> str:
    """
    Convert Prisma camelCase/PascalCase names to SQLModel snake_case.

    Parameters
    ----------
    prisma_name : str
        Prisma-style field or model name (e.g., "guildId", "Guild").

    Returns
    -------
    str
        SQLModel-style snake_case name (e.g., "guild_id", "guild").

    Examples
    --------
    >>> convert_prisma_to_sqlmodel_name("guildId")
    'guild_id'
    >>> convert_prisma_to_sqlmodel_name("caseType")
    'case_type'
    >>> convert_prisma_to_sqlmodel_name("Guild")
    'guild'
    """
    if not prisma_name:
        return prisma_name

    # Handle PascalCase model names (e.g., "Guild" -> "guild")
    if prisma_name[0].isupper() and len(prisma_name) > 1:
        prisma_name = prisma_name[0].lower() + prisma_name[1:]

    # Convert camelCase to snake_case
    result: list[str] = []
    for i, char in enumerate(prisma_name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())

    return "".join(result)


def transform_enum_value(
    old_value: str | None,
    enum_mapping: dict[str, str],
    default: str | None = None,
) -> str | None:
    """
    Transform enum value from old format to new format.

    Parameters
    ----------
    old_value : str | None
        Old enum value to transform.
    enum_mapping : dict[str, str]
        Mapping from old enum values to new enum values.
    default : str | None, optional
        Default value if mapping not found (default: None).

    Returns
    -------
    str | None
        Transformed enum value, or default if not found.

    Examples
    --------
    >>> mapping = {"BAN": "ban", "KICK": "kick"}
    >>> transform_enum_value("BAN", mapping)
    'ban'
    >>> transform_enum_value("UNKNOWN", mapping, "ban")
    'ban'
    """
    if old_value is None:
        return default

    # Try exact match first
    if old_value in enum_mapping:
        return enum_mapping[old_value]

    # Try case-insensitive match
    for old_key, new_value in enum_mapping.items():
        if old_key.lower() == old_value.lower():
            return new_value

    # Try converting to new format (camelCase -> UPPER_SNAKE_CASE)
    converted = old_value.upper().replace("-", "_")
    if converted in enum_mapping:
        return enum_mapping[converted]

    logger.warning(
        f"Enum value '{old_value}' not found in mapping, using default: {default}",
    )
    return default


def normalize_datetime(dt: datetime | str | None) -> datetime | None:
    """
    Normalize datetime to UTC timezone-aware datetime.

    Parameters
    ----------
    dt : datetime | str | None
        Datetime to normalize. Can be datetime object, ISO string, or None.

    Returns
    -------
    datetime | None
        UTC timezone-aware datetime, or None if input is None.

    Notes
    -----
    SQLModel models expect timezone-aware datetimes in UTC.
    This function ensures all datetimes are properly normalized.
    """
    if dt is None:
        return None

    # Handle string input
    if isinstance(dt, str):
        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00", 1))
        except ValueError:
            logger.warning(f"Failed to parse datetime string: {dt}")
            return None

    # Handle naive datetime (assume UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to UTC
    dt = dt.astimezone(UTC)

    # Remove timezone info for database storage (SQLModel handles this)
    return dt.replace(tzinfo=None)


def safe_json_parse(value: Any) -> dict[str, Any] | list[Any] | None:
    """
    Safely parse JSON value with error handling.

    Parameters
    ----------
    value : Any
        Value to parse. Can be dict, list, str, or None.

    Returns
    -------
    dict[str, Any] | list[Any] | None
        Parsed JSON value, or None if parsing fails.

    Examples
    --------
    >>> safe_json_parse('{"key": "value"}')
    {'key': 'value'}
    >>> safe_json_parse([1, 2, 3])
    [1, 2, 3]
    >>> safe_json_parse(None)
    None
    """
    result = None

    if value is None:
        pass  # result remains None
    elif isinstance(value, dict):
        result = cast(dict[str, Any], value)
    elif isinstance(value, list):
        result = cast(list[Any], value)
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                result = cast(dict[str, Any], parsed)
            elif isinstance(parsed, list):
                result = cast(list[Any], parsed)
            else:
                logger.warning(f"Parsed JSON is not dict or list: {type(parsed)}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse JSON: {value[:100]}... Error: {e}")
    else:
        logger.warning(f"Unexpected JSON value type: {type(value)}")

    return result


def sanitize_database_url(url: str) -> str:
    """
    Sanitize database URL for logging (remove password).

    Parameters
    ----------
    url : str
        Database connection URL.

    Returns
    -------
    str
        Sanitized URL with password replaced with ***.
    """
    try:
        # Split on @ to separate credentials from host
        parts = url.split("@")
        if len(parts) == 2:
            # Split credentials part
            creds = parts[0].split("://")
            if len(creds) == 2:
                # Replace password with ***
                scheme = creds[0]
                user_pass = creds[1].split(":")
                if len(user_pass) >= 2:
                    user = user_pass[0]
                    return f"{scheme}://{user}:***@{parts[1]}"
    except Exception:
        return "***"
    else:
        return "***"
