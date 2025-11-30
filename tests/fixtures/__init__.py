"""Test fixtures package.

This package contains all test fixtures organized by category:
- database_fixtures: Database and PGlite-related fixtures
- test_data_fixtures: Sample data fixtures and test constants
- sentry_fixtures: Sentry and Discord mock fixtures

Fixtures are automatically discovered by pytest when imported in conftest.py.
"""

# Import modules to register fixtures with pytest
# These imports are for side effects (pytest fixture registration)
from . import database_fixtures  # noqa: F401  # type: ignore[reportUnusedImport]
from . import test_data_fixtures  # noqa: F401  # type: ignore[reportUnusedImport]
from . import sentry_fixtures  # noqa: F401  # type: ignore[reportUnusedImport]

# Export test constants and utility functions
from .test_data_fixtures import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    TEST_MODERATOR_ID,
    TEST_USER_ID,
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
