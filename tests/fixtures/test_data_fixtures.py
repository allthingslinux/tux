"""Test data fixtures for consistent test data."""

import pytest
from typing import Any
from loguru import logger

from tux.database.controllers import GuildConfigController, GuildController

# Test constants
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321
TEST_MODERATOR_ID = 555666777888999000


@pytest.fixture(scope="function")
async def sample_guild(guild_controller: GuildController) -> Any:
    """Sample guild for testing."""
    logger.info("🔧 Creating sample guild")
    guild = await guild_controller.insert_guild_by_id(TEST_GUILD_ID)
    logger.info(f"✅ Created sample guild with ID: {guild.id}")
    return guild


@pytest.fixture(scope="function")
async def sample_guild_with_config(
    guild_controller: GuildController,
    guild_config_controller: GuildConfigController,
) -> dict[str, Any]:
    """Sample guild with config for testing."""
    logger.info("🔧 Creating sample guild with config")

    # Create guild
    guild = await guild_controller.insert_guild_by_id(TEST_GUILD_ID)

    # Create config
    config = await guild_config_controller.insert_guild_config(
        guild_id=TEST_GUILD_ID,
        prefix="!",
    )

    result = {"guild": guild, "config": config}
    logger.info(f"✅ Created sample guild with config: {guild.id}")
    return result


def validate_guild_structure(guild: Any) -> bool:
    """Validate guild model structure and required fields."""
    return (
        hasattr(guild, "id") and
        hasattr(guild, "case_count") and
        hasattr(guild, "guild_joined_at") and
        isinstance(guild.id, int) and
        isinstance(guild.case_count, int)
    )


def validate_guild_config_structure(config: Any) -> bool:
    """Validate guild config model structure and required fields."""
    return (
        hasattr(config, "id") and
        hasattr(config, "prefix") and
        isinstance(config.id, int) and
        (config.prefix is None or isinstance(config.prefix, str))
    )


def validate_relationship_integrity(guild: Any, config: Any) -> bool:
    """Validate relationship integrity between guild and config."""
    return guild.id == config.id
