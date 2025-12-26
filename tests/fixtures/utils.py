"""Test utility functions for validation, mock data creation, and common operations."""

from typing import Any


# Mock data factory functions (inspired by organizex patterns)
def create_mock_guild(**overrides) -> dict[str, Any]:
    """Create mock guild data for testing.

    Parameters
    ----------
    **overrides : dict
        Override default values.

    Returns
    -------
    dict[str, Any]
        Mock guild data dictionary.
    """
    default_data = {
        "id": 123456789012345678,
        "name": "Test Guild",
        "member_count": 100,
        "owner_id": 987654321098765432,
    }
    default_data.update(overrides)
    return default_data


def create_mock_user(**overrides) -> dict[str, Any]:
    """Create mock Discord user data for testing.

    Parameters
    ----------
    **overrides : dict
        Override default values.

    Returns
    -------
    dict[str, Any]
        Mock user data dictionary.
    """
    default_data = {
        "id": 987654321098765432,
        "name": "testuser",
        "discriminator": "1234",
        "display_name": "Test User",
        "bot": False,
        "mention": "<@987654321098765432>",
    }
    default_data.update(overrides)
    return default_data


def create_mock_channel(**overrides) -> dict[str, Any]:
    """Create mock Discord channel data for testing.

    Parameters
    ----------
    **overrides : dict
        Override default values.

    Returns
    -------
    dict[str, Any]
        Mock channel data dictionary.
    """
    default_data = {
        "id": 876543210987654321,
        "name": "test-channel",
        "mention": "<#876543210987654321>",
        "type": "text",
    }
    default_data.update(overrides)
    return default_data


def create_mock_interaction(**overrides) -> dict[str, Any]:
    """Create mock Discord interaction data for testing.

    Parameters
    ----------
    **overrides : dict
        Override default values.

    Returns
    -------
    dict[str, Any]
        Mock interaction data dictionary.
    """
    default_data = {
        "user": create_mock_user(),
        "guild": create_mock_guild(),
        "guild_id": 123456789012345678,
        "channel": create_mock_channel(),
        "channel_id": 876543210987654321,
        "command": {"qualified_name": "test_command"},
    }
    default_data.update(overrides)
    return default_data


# Validation functions
def validate_guild_structure(guild) -> bool:
    """Validate guild model structure and required fields.

    Parameters
    ----------
    guild : Any
        Guild object to validate.

    Returns
    -------
    bool
        True if guild has all required fields with correct types.
    """
    return (
        hasattr(guild, "id") and
        hasattr(guild, "case_count") and
        hasattr(guild, "guild_joined_at") and
        isinstance(guild.id, int) and
        isinstance(guild.case_count, int)
    )


def validate_guild_config_structure(config) -> bool:
    """Validate guild config model structure and required fields.

    Parameters
    ----------
    config : Any
        Guild config object to validate.

    Returns
    -------
    bool
        True if config has all required fields with correct types.
    """
    return (
        hasattr(config, "id") and
        hasattr(config, "prefix") and
        isinstance(config.id, int) and
        (config.prefix is None or isinstance(config.prefix, str))
    )


def validate_relationship_integrity(guild, config) -> bool:
    """Validate relationship integrity between guild and config.

    Parameters
    ----------
    guild : Any
        Guild object.
    config : Any
        Guild config object.

    Returns
    -------
    bool
        True if relationship integrity is maintained.
    """
    return guild.id == config.id
