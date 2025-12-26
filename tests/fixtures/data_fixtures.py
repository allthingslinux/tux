"""Test data fixtures for consistent test data."""

import pytest
from typing import Any

from tux.database.controllers import GuildConfigController, GuildController

# Test constants
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321
TEST_MODERATOR_ID = 555666777888999000


@pytest.fixture(scope="function")
async def sample_guild(guild_controller: GuildController) -> Any:
    """Sample guild for testing."""
    guild = await guild_controller.insert_guild_by_id(TEST_GUILD_ID)
    return guild


@pytest.fixture(scope="function")
async def sample_guild_with_config(
    guild_controller: GuildController,
    guild_config_controller: GuildConfigController,
) -> dict[str, Any]:
    """Sample guild with config for testing."""
    # Create guild
    guild = await guild_controller.insert_guild_by_id(TEST_GUILD_ID)

    # Create config
    config = await guild_config_controller.insert_guild_config(
        guild_id=TEST_GUILD_ID,
        prefix="!",
    )

    result = {"guild": guild, "config": config}
    return result
