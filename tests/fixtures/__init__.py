"""Test fixtures package.

This package contains all test fixtures organized by category:
- database_fixtures: Database and PGlite-related fixtures
- data_fixtures: Sample data fixtures and test constants
- sentry_fixtures: Sentry and Discord mock fixtures
- utils: Validation and utility functions

Fixtures are automatically discovered by pytest when imported in conftest.py.
"""

# Export test constants and utility functions
from .data_fixtures import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    TEST_MODERATOR_ID,
    TEST_USER_ID,
)
from .utils import (
    validate_guild_config_structure,
    validate_guild_structure,
    validate_relationship_integrity,
)

__all__ = [
    # Test constants
    "TEST_CHANNEL_ID",
    "TEST_GUILD_ID",
    "TEST_MODERATOR_ID",
    "TEST_USER_ID",
    # Validation functions
    "validate_guild_config_structure",
    "validate_guild_structure",
    "validate_relationship_integrity",
]
