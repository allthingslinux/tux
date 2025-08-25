"""
Database test fixtures and utilities.

This module provides common fixtures, test data, and utilities for database testing
across all test categories (unit, integration, e2e).
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from sqlmodel import SQLModel

from tux.database.models import (
    Guild, GuildConfig, Snippet, Reminder, Case, CaseType,
    Note, GuildPermission, PermissionType, AccessType, AFK, Levels,
    Starboard, StarboardMessage,
)


# Test data constants
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 555666777888999000
TEST_MESSAGE_ID = 111222333444555666


@pytest.fixture
async def in_memory_db() -> AsyncGenerator[AsyncEngine]:
    """Create an in-memory SQLite database for testing."""
    database_url = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(database_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def temp_file_db(tmp_path: Path) -> AsyncGenerator[AsyncEngine]:
    """Create a temporary file-based SQLite database for testing."""
    db_file = tmp_path / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(database_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def session_factory(in_memory_db: AsyncEngine) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    """Create a session factory for testing."""
    factory = async_sessionmaker(in_memory_db, expire_on_commit=False)
    yield factory


@pytest.fixture
async def db_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
    """Create a database session for testing."""
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


# Test data fixtures
@pytest.fixture
def sample_guild() -> Guild:
    """Create a sample guild for testing."""
    return Guild(
        guild_id=TEST_GUILD_ID,
        guild_joined_at=None,  # Will be set automatically
    )


@pytest.fixture
def sample_guild_config() -> GuildConfig:
    """Create a sample guild config for testing."""
    return GuildConfig(
        guild_id=TEST_GUILD_ID,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        starboard_channel_id=TEST_CHANNEL_ID + 2,
    )


@pytest.fixture
def sample_snippet() -> Snippet:
    """Create a sample snippet for testing."""
    return Snippet(
        snippet_name="test_snippet",
        snippet_content="This is a test snippet content",
        snippet_user_id=TEST_USER_ID,
        guild_id=TEST_GUILD_ID,
        uses=5,
        locked=False,
    )


@pytest.fixture
def sample_reminder() -> Reminder:
    """Create a sample reminder for testing."""
    from datetime import datetime, UTC
    return Reminder(
        reminder_content="Test reminder",
        reminder_expires_at=datetime.now(UTC),
        reminder_channel_id=TEST_CHANNEL_ID,
        reminder_user_id=TEST_USER_ID,
        reminder_sent=False,
        guild_id=TEST_GUILD_ID,
    )


@pytest.fixture
def sample_case() -> Case:
    """Create a sample case for testing."""
    return Case(
        case_status=True,
        case_reason="Test case reason",
        case_moderator_id=TEST_USER_ID,
        case_user_id=TEST_USER_ID + 1,
        case_user_roles=[TEST_USER_ID + 2, TEST_USER_ID + 3],
        case_number=1,
        guild_id=TEST_GUILD_ID,
    )


@pytest.fixture
def sample_note() -> Note:
    """Create a sample note for testing."""
    return Note(
        note_content="Test note content",
        note_moderator_id=TEST_USER_ID,
        note_user_id=TEST_USER_ID + 1,
        note_number=1,
        guild_id=TEST_GUILD_ID,
    )


@pytest.fixture
def sample_guild_permission() -> GuildPermission:
    """Create a sample guild permission for testing."""
    return GuildPermission(
        id=1,
        guild_id=TEST_GUILD_ID,
        permission_type=PermissionType.MEMBER,
        access_type=AccessType.WHITELIST,
        target_id=TEST_USER_ID,
        target_name="Test User",
        is_active=True,
    )


@pytest.fixture
def sample_afk() -> AFK:
    """Create a sample AFK record for testing."""
    from datetime import datetime, UTC
    return AFK(
        member_id=TEST_USER_ID,
        nickname="TestUser",
        reason="Testing AFK functionality",
        since=datetime.now(UTC),
        guild_id=TEST_GUILD_ID,
        enforced=False,
        perm_afk=False,
    )


@pytest.fixture
def sample_levels() -> Levels:
    """Create a sample levels record for testing."""
    from datetime import datetime, UTC
    return Levels(
        member_id=TEST_USER_ID,
        guild_id=TEST_GUILD_ID,
        xp=150.5,
        level=3,
        blacklisted=False,
        last_message=datetime.now(UTC),
    )


@pytest.fixture
def sample_starboard() -> Starboard:
    """Create a sample starboard for testing."""
    return Starboard(
        guild_id=TEST_GUILD_ID,
        starboard_channel_id=TEST_CHANNEL_ID,
        starboard_emoji="⭐",
        starboard_threshold=3,
    )


@pytest.fixture
def sample_starboard_message() -> StarboardMessage:
    """Create a sample starboard message for testing."""
    from datetime import datetime, UTC
    return StarboardMessage(
        message_id=TEST_MESSAGE_ID,
        message_content="This is a test message for starboard",
        message_expires_at=datetime.now(UTC),
        message_channel_id=TEST_CHANNEL_ID + 1,
        message_user_id=TEST_USER_ID,
        message_guild_id=TEST_GUILD_ID,
        star_count=5,
        starboard_message_id=TEST_MESSAGE_ID + 1,
    )


# Utility functions
async def create_test_data(session: AsyncSession) -> dict[str, Any]:
    """Create a comprehensive set of test data for testing."""
    # Create base guild
    guild = Guild(guild_id=TEST_GUILD_ID)
    session.add(guild)

    # Create guild config
    guild_config = GuildConfig(
        guild_id=TEST_GUILD_ID,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
    )
    session.add(guild_config)

    await session.commit()

    return {
        'guild': guild,
        'guild_config': guild_config,
    }


async def cleanup_test_data(session: AsyncSession) -> None:
    """Clean up test data after tests."""
    # Get all tables that exist in the database
    result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    existing_tables = {row[0] for row in result.fetchall()}

    # Tables to clean up in reverse order of dependencies
    tables_to_cleanup = [
        "starboard_message", "starboard", "levels", "afk", "guild_permission",
        "note", "cases", "reminder", "snippet", "guild_config", "guild",
    ]

    # Only delete from tables that exist
    for table in tables_to_cleanup:
        if table in existing_tables:
            await session.execute(text(f"DELETE FROM {table}"))

    await session.commit()


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("DEV_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("PROD_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


# Test database URL configurations
TEST_DATABASE_URLS = {
    "sqlite_memory": "sqlite+aiosqlite:///:memory:",
    "sqlite_file": "sqlite+aiosqlite:///test.db",
    "postgres_mock": "postgresql+asyncpg://test:test@localhost:5432/test",
}


@pytest.fixture(params=list(TEST_DATABASE_URLS.values()))
def database_url(request: pytest.FixtureRequest) -> str:
    """Parameterized fixture for different database URLs."""
    return request.param
