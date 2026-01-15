"""Test data fixtures for consistent test data."""

import pytest
from typing import Any

from tux.database.controllers import GuildConfigController, GuildController

# Import constants from separate module to avoid assertion rewriting issues
from tests.constants import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    TEST_MODERATOR_ID,
    TEST_USER_ID,
)


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
