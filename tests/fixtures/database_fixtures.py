"""
🚀 Database Test Fixtures - Hybrid Architecture

Provides test data fixtures for both unit and integration testing:
- UNIT FIXTURES: Fast sync SQLModel operations using py-pglite
- INTEGRATION FIXTURES: Async controller operations using DatabaseService

Key Features:
- Pre-populated test data using real database operations
- Proper fixture scoping for performance
- Clean separation between unit and integration fixtures
- Shared SQLModel definitions across both approaches
"""

from typing import Any
import pytest
import pytest_asyncio
from sqlmodel import Session

from tux.database.service import DatabaseService
from tux.database.models.models import Guild, GuildConfig

# Test constants - Discord-compatible snowflake IDs
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321
TEST_MODERATOR_ID = 555666777888999000


# =============================================================================
# UNIT TEST FIXTURES - Sync SQLModel + py-pglite
# =============================================================================

@pytest.fixture
def sample_guild(db_session: Session) -> Guild:
    """Sample guild created through sync SQLModel session."""
    guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
    db_session.add(guild)
    db_session.commit()
    db_session.refresh(guild)
    return guild


@pytest.fixture
def sample_guild_config(db_session: Session, sample_guild: Guild) -> GuildConfig:
    """Sample guild config created through sync SQLModel session."""
    config = GuildConfig(
        guild_id=sample_guild.guild_id,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        starboard_channel_id=TEST_CHANNEL_ID + 2,
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


@pytest.fixture
def sample_guild_with_config(db_session: Session) -> dict[str, Any]:
    """Sample guild with config created through sync SQLModel."""
    # Create guild
    guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
    db_session.add(guild)
    db_session.commit()
    db_session.refresh(guild)

    # Create config
    config = GuildConfig(
        guild_id=guild.guild_id,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        starboard_channel_id=TEST_CHANNEL_ID + 2,
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)

    return {
        'guild': guild,
        'config': config,
        'guild_id': TEST_GUILD_ID,
        'channel_ids': {
            'mod_log': TEST_CHANNEL_ID,
            'audit_log': TEST_CHANNEL_ID + 1,
            'starboard': TEST_CHANNEL_ID + 2,
        },
    }


@pytest.fixture
def multiple_guilds(db_session: Session) -> list[Guild]:
    """Multiple guilds for testing bulk operations."""
    guilds: list[Guild] = []
    for i in range(5):
        guild_id = TEST_GUILD_ID + i
        guild = Guild(guild_id=guild_id, case_count=i)
        db_session.add(guild)
        guilds.append(guild)

    db_session.commit()

    # Refresh all guilds
    for guild in guilds:
        db_session.refresh(guild)

    return guilds


@pytest.fixture
def populated_test_database(db_session: Session) -> dict[str, Any]:
    """Fully populated test database with multiple entities."""
    # Create multiple guilds with configs
    guilds_data = []

    for i in range(3):
        guild_id = TEST_GUILD_ID + i

        # Create guild
        guild = Guild(guild_id=guild_id, case_count=i)
        db_session.add(guild)

        # Create config
        config = GuildConfig(
            guild_id=guild_id,
            prefix=f"!{i}",
            mod_log_id=TEST_CHANNEL_ID + i,
            audit_log_id=TEST_CHANNEL_ID + i + 10,
        )
        db_session.add(config)

        guilds_data.append({
            'guild': guild,
            'config': config,
            'guild_id': guild_id,
        })

    db_session.commit()

    # Refresh all entities
    for data in guilds_data:
        db_session.refresh(data['guild'])
        db_session.refresh(data['config'])

    return {
        'guilds': guilds_data,
        'total_guilds': len(guilds_data),
        'test_constants': {
            'base_guild_id': TEST_GUILD_ID,
            'base_channel_id': TEST_CHANNEL_ID,
        },
    }


# =============================================================================
# INTEGRATION TEST FIXTURES - Async DatabaseService + Real PostgreSQL
# =============================================================================

@pytest_asyncio.fixture
async def async_sample_guild(async_db_service: DatabaseService) -> Guild:
    """Sample guild created through async controller."""
    return await async_db_service.guild.get_or_create_guild(guild_id=TEST_GUILD_ID)


@pytest_asyncio.fixture
async def async_sample_guild_config(async_db_service: DatabaseService) -> dict[str, Any]:
    """Sample guild with config created through async controllers."""
    # Create guild through controller
    guild = await async_db_service.guild.get_or_create_guild(guild_id=TEST_GUILD_ID)

    # Create config through controller
    config = await async_db_service.guild_config.get_or_create_config(
        guild_id=guild.guild_id,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        starboard_channel_id=TEST_CHANNEL_ID + 2,
    )

    return {
        'guild': guild,
        'config': config,
        'guild_id': TEST_GUILD_ID,
        'guild_controller': async_db_service.guild,
        'guild_config_controller': async_db_service.guild_config,
        'channel_ids': {
            'mod_log': TEST_CHANNEL_ID,
            'audit_log': TEST_CHANNEL_ID + 1,
            'starboard': TEST_CHANNEL_ID + 2,
        },
    }


@pytest_asyncio.fixture
async def async_multiple_guilds(async_db_service: DatabaseService) -> list[Guild]:
    """Multiple guilds created through async controllers."""
    guilds: list[Guild] = []
    for i in range(5):
        guild_id = TEST_GUILD_ID + i
        guild = await async_db_service.guild.get_or_create_guild(guild_id=guild_id)
        guilds.append(guild)
    return guilds


@pytest_asyncio.fixture
async def async_performance_test_setup(async_db_service: DatabaseService) -> dict[str, Any]:
    """Performance test setup with async controllers."""
    # Create base guild and config through controllers
    guild = await async_db_service.guild.get_or_create_guild(guild_id=TEST_GUILD_ID)
    config = await async_db_service.guild_config.get_or_create_config(
        guild_id=guild.guild_id,
        prefix="!perf",
        mod_log_id=TEST_CHANNEL_ID,
    )

    return {
        'guild': guild,
        'config': config,
        'db_service': async_db_service,
        'test_constants': {
            'guild_id': TEST_GUILD_ID,
            'user_id': TEST_USER_ID,
            'channel_id': TEST_CHANNEL_ID,
            'moderator_id': TEST_MODERATOR_ID,
        },
    }


# =============================================================================
# RELATIONSHIP TEST FIXTURES
# =============================================================================

@pytest.fixture
def guild_relationships_setup(db_session: Session) -> dict[str, Any]:
    """Setup for testing model relationships through sync SQLModel."""
    # Create guild with full config
    guild = Guild(guild_id=TEST_GUILD_ID, case_count=0)
    db_session.add(guild)
    db_session.commit()
    db_session.refresh(guild)

    config = GuildConfig(
        guild_id=guild.guild_id,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        join_log_id=TEST_CHANNEL_ID + 2,
        private_log_id=TEST_CHANNEL_ID + 3,
        report_log_id=TEST_CHANNEL_ID + 4,
        dev_log_id=TEST_CHANNEL_ID + 5,
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)

    return {
        'guild': guild,
        'config': config,
        'session': db_session,
        'relationship_data': {
            'guild_to_config': guild.guild_id == config.guild_id,
            'log_channels': {
                'mod_log_id': config.mod_log_id,
                'audit_log_id': config.audit_log_id,
                'join_log_id': config.join_log_id,
                'private_log_id': config.private_log_id,
                'report_log_id': config.report_log_id,
                'dev_log_id': config.dev_log_id,
            },
        },
    }


@pytest_asyncio.fixture
async def async_guild_relationships_setup(async_db_service: DatabaseService) -> dict[str, Any]:
    """Setup for testing relationships through async controllers."""
    # Create guild with full config through controllers
    guild = await async_db_service.guild.get_or_create_guild(guild_id=TEST_GUILD_ID)

    config = await async_db_service.guild_config.get_or_create_config(
        guild_id=guild.guild_id,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        join_log_id=TEST_CHANNEL_ID + 2,
        private_log_id=TEST_CHANNEL_ID + 3,
        report_log_id=TEST_CHANNEL_ID + 4,
        dev_log_id=TEST_CHANNEL_ID + 5,
    )

    return {
        'guild': guild,
        'config': config,
        'db_service': async_db_service,
        'relationship_data': {
            'guild_to_config': guild.guild_id == config.guild_id,
            'log_channels': {
                'mod_log_id': config.mod_log_id,
                'audit_log_id': config.audit_log_id,
                'join_log_id': config.join_log_id,
                'private_log_id': config.private_log_id,
                'report_log_id': config.report_log_id,
                'dev_log_id': config.dev_log_id,
            },
        },
    }


# =============================================================================
# ERROR TEST FIXTURES
# =============================================================================

@pytest.fixture
def invalid_guild_scenario() -> dict[str, Any]:
    """Setup for testing invalid guild scenarios."""
    return {
        'invalid_guild_id': 999999999999999999,  # Non-existent guild
        'valid_guild_id': TEST_GUILD_ID,
        'test_prefix': "!invalid",
    }


@pytest_asyncio.fixture
async def async_invalid_guild_scenario(async_db_service: DatabaseService) -> dict[str, Any]:
    """Setup for testing invalid guild scenarios with async controllers."""
    return {
        'guild_config_controller': async_db_service.guild_config,
        'invalid_guild_id': 999999999999999999,  # Non-existent guild
        'valid_guild_id': TEST_GUILD_ID,
        'test_prefix': "!invalid",
    }


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_guild_structure(guild: Guild) -> bool:
    """Validate guild model structure and required fields."""
    return (
        hasattr(guild, 'guild_id') and
        hasattr(guild, 'case_count') and
        hasattr(guild, 'guild_joined_at') and
        isinstance(guild.guild_id, int) and
        isinstance(guild.case_count, int)
    )


def validate_guild_config_structure(config: GuildConfig) -> bool:
    """Validate guild config model structure and required fields."""
    return (
        hasattr(config, 'guild_id') and
        hasattr(config, 'prefix') and
        isinstance(config.guild_id, int) and
        (config.prefix is None or isinstance(config.prefix, str))
    )


def validate_relationship_integrity(guild: Guild, config: GuildConfig) -> bool:
    """Validate relationship integrity between guild and config."""
    return guild.guild_id == config.guild_id


# =============================================================================
# BENCHMARK FIXTURES
# =============================================================================

@pytest.fixture
def benchmark_data_unit(db_session: Session) -> dict[str, Any]:
    """Benchmark data setup for unit tests."""
    # Create multiple entities for performance testing
    guilds = []
    configs = []

    for i in range(10):
        guild_id = TEST_GUILD_ID + i

        guild = Guild(guild_id=guild_id, case_count=i)
        db_session.add(guild)
        guilds.append(guild)

        config = GuildConfig(
            guild_id=guild_id,
            prefix=f"!bench{i}",
            mod_log_id=TEST_CHANNEL_ID + i,
        )
        db_session.add(config)
        configs.append(config)

    db_session.commit()

    return {
        'guilds': guilds,
        'configs': configs,
        'session': db_session,
        'count': 10,
    }


@pytest_asyncio.fixture
async def async_benchmark_data(async_db_service: DatabaseService) -> dict[str, Any]:
    """Benchmark data setup for integration tests."""
    guilds = []
    configs = []

    for i in range(10):
        guild_id = TEST_GUILD_ID + i

        guild = await async_db_service.guild.get_or_create_guild(guild_id=guild_id)
        guilds.append(guild)

        config = await async_db_service.guild_config.get_or_create_config(
            guild_id=guild_id,
            prefix=f"!bench{i}",
            mod_log_id=TEST_CHANNEL_ID + i,
        )
        configs.append(config)

    return {
        'guilds': guilds,
        'configs': configs,
        'db_service': async_db_service,
        'count': 10,
    }


# =============================================================================
# LEGACY COMPATIBILITY - For Gradual Migration
# =============================================================================

def sample_guild_dict() -> dict[str, Any]:
    """Legacy dict-based guild fixture (DEPRECATED - use SQLModel fixtures)."""
    return {
        'guild_id': TEST_GUILD_ID,
        'case_count': 0,
        'guild_joined_at': None,
    }


def sample_guild_config_dict() -> dict[str, Any]:
    """Legacy dict-based config fixture (DEPRECATED - use SQLModel fixtures)."""
    return {
        'guild_id': TEST_GUILD_ID,
        'prefix': "!",
        'mod_log_id': TEST_CHANNEL_ID,
        'audit_log_id': TEST_CHANNEL_ID + 1,
        'starboard_channel_id': TEST_CHANNEL_ID + 2,
    }
