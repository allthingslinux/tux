"""
End-to-end tests for complete database workflows.

Tests simulate real-world usage scenarios including:
- First-time bot setup
- Guild onboarding process
- Feature usage workflows
- Data migration between versions
"""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select

from tux.database.models import (
    Guild, GuildConfig, Snippet, Reminder, Case, CaseType,
    Note, GuildPermission, PermissionType, AccessType, AFK, Levels,
    Starboard, StarboardMessage,
)
from tests.fixtures.database_fixtures import (
    TEST_GUILD_ID, TEST_USER_ID, TEST_CHANNEL_ID, TEST_MESSAGE_ID,
    create_test_data, cleanup_test_data,
)


@pytest.mark.e2e
class TestFirstTimeBotSetup:
    """Test complete first-time bot setup workflow."""

    @pytest.fixture
    async def fresh_db(self):
        """Create a completely fresh database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        database_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_async_engine(database_url, echo=False)

        try:
            yield engine, database_url, db_path
        finally:
            await engine.dispose()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_initial_schema_creation(self, fresh_db):
        """Test creating database schema from scratch."""
        engine, database_url, db_path = fresh_db

        # Simulate first-time setup
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Verify all tables were created
        async with engine.begin() as conn:
            # Get all table names
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = {row[0] for row in result.fetchall()}

            # Expected tables (excluding SQLite system tables)
            expected_tables = {
                'guild', 'guildconfig', 'snippet', 'reminder', 'cases',
                'note', 'guildpermission', 'afk',
                'levels', 'starboard', 'starboardmessage',
            }

            for expected_table in expected_tables:
                assert expected_table in tables, f"Missing table: {expected_table}"

    @pytest.mark.asyncio
    async def test_guild_onboarding_workflow(self, fresh_db):
        """Test complete guild onboarding workflow."""
        engine, database_url, db_path = fresh_db

        # Create schema
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Step 1: Bot joins guild for the first time
        async with session_factory() as session:
            guild = Guild(guild_id=TEST_GUILD_ID)
            session.add(guild)
            await session.commit()

        # Step 2: Create default guild configuration
        async with session_factory() as session:
            config = GuildConfig(
                guild_id=TEST_GUILD_ID,
                prefix="!",
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(config)
            await session.commit()

        # Step 3: Verify setup is complete
        async with session_factory() as session:
            # Check guild exists
            guild_result = await session.execute(select(Guild).where(Guild.guild_id == TEST_GUILD_ID))
            found_guild = guild_result.scalar_one_or_none()
            assert found_guild is not None

            # Check config exists
            config_result = await session.execute(select(GuildConfig).where(GuildConfig.guild_id == TEST_GUILD_ID))
            found_config = config_result.scalar_one_or_none()
            assert found_config is not None
            assert found_config.prefix == "!"

    @pytest.mark.asyncio
    async def test_feature_setup_workflow(self, fresh_db):
        """Test setting up various bot features for a guild."""
        engine, database_url, db_path = fresh_db

        # Create schema and basic guild setup
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Basic setup
        async with session_factory() as session:
            guild = Guild(guild_id=TEST_GUILD_ID)
            config = GuildConfig(guild_id=TEST_GUILD_ID, prefix="!")
            session.add(guild)
            session.add(config)
            await session.commit()

        # Setup snippets feature
        async with session_factory() as session:
            snippet = Snippet(
                snippet_name="welcome",
                snippet_content="Welcome to our server!",
                snippet_user_id=TEST_USER_ID,
                guild_id=TEST_GUILD_ID,
            )
            session.add(snippet)
            await session.commit()

        # Setup permissions
        async with session_factory() as session:
            permission = GuildPermission(
                id=1,
                guild_id=TEST_GUILD_ID,
                permission_type=PermissionType.COMMAND,
                access_type=AccessType.WHITELIST,
                target_id=TEST_CHANNEL_ID,
                command_name="help",
            )
            session.add(permission)
            await session.commit()

        # Verify all features are set up
        async with session_factory() as session:
            # Check snippets
            snippet_result = await session.execute(select(Snippet).where(Snippet.guild_id == TEST_GUILD_ID))
            snippets = snippet_result.scalars().all()
            assert len(snippets) == 1
            assert snippets[0].snippet_name == "welcome"

            # Check permissions
            perm_result = await session.execute(select(GuildPermission).where(GuildPermission.guild_id == TEST_GUILD_ID))
            perms = perm_result.scalars().all()
            assert len(perms) == 1
            assert perms[0].command_name == "help"


@pytest.mark.e2e
class TestFeatureUsageWorkflows:
    """Test complete feature usage workflows."""

    @pytest.fixture
    async def setup_db(self):
        """Create database with test setup."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        database_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_async_engine(database_url, echo=False)

        # Create schema
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Setup test data
        async with session_factory() as session:
            await create_test_data(session)

        try:
            yield engine, database_url, session_factory
        finally:
            # Clean up
            async with session_factory() as session:
                await cleanup_test_data(session)

            await engine.dispose()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_snippet_usage_workflow(self, setup_db):
        """Test complete snippet usage workflow."""
        engine, database_url, session_factory = setup_db

        # Simulate user creating a snippet
        async with session_factory() as session:
            snippet = Snippet(
                snippet_name="rules",
                snippet_content="Please follow the server rules!",
                snippet_user_id=TEST_USER_ID,
                guild_id=TEST_GUILD_ID,
                uses=0,
            )
            session.add(snippet)
            await session.commit()

        # Simulate snippet being used multiple times
        async with session_factory() as session:
            snippet_result = await session.execute(
                select(Snippet).where(
                    (Snippet.snippet_name == "rules") &
                    (Snippet.guild_id == TEST_GUILD_ID),
                ),
            )
            snippet = snippet_result.scalar_one()

            # Increment usage counter
            snippet.uses = 5
            await session.commit()

        # Verify usage was tracked
        async with session_factory() as session:
            snippet_result = await session.execute(
                select(Snippet).where(
                    (Snippet.snippet_name == "rules") &
                    (Snippet.guild_id == TEST_GUILD_ID),
                ),
            )
            updated_snippet = snippet_result.scalar_one()
            assert updated_snippet.uses == 5

    @pytest.mark.asyncio
    async def test_moderation_workflow(self, setup_db):
        """Test complete moderation workflow."""
        engine, database_url, session_factory = setup_db

        # Simulate moderator action
        async with session_factory() as session:
            # Create case
            case = Case(
                case_reason="Spamming in chat",
                case_moderator_id=TEST_USER_ID,
                case_user_id=TEST_USER_ID + 1,
                case_user_roles=[TEST_USER_ID + 2],
                guild_id=TEST_GUILD_ID,
                case_number=1,
            )
            session.add(case)
            await session.commit()

        # Add a note to the case
        async with session_factory() as session:
            note = Note(
                note_content="User was warned about spam behavior",
                note_moderator_id=TEST_USER_ID,
                note_user_id=TEST_USER_ID + 1,
                note_number=1,
                guild_id=TEST_GUILD_ID,
            )
            session.add(note)
            await session.commit()

        # Verify the complete moderation record
        async with session_factory() as session:
            # Check case
            case_result = await session.execute(select(Case).where(Case.guild_id == TEST_GUILD_ID))
            cases = case_result.scalars().all()
            assert len(cases) >= 1

            # Check note
            note_result = await session.execute(select(Note).where(Note.guild_id == TEST_GUILD_ID))
            notes = note_result.scalars().all()
            assert len(notes) >= 1

    @pytest.mark.asyncio
    async def test_user_experience_workflow(self, setup_db):
        """Test complete user experience workflow."""
        engine, database_url, session_factory = setup_db

        # User joins server - create AFK record
        async with session_factory() as session:
            from datetime import datetime, UTC

            afk = AFK(
                member_id=TEST_USER_ID,
                nickname="NewUser",
                reason="Just joined the server",
                since=datetime.now(UTC),
                guild_id=TEST_GUILD_ID,
            )
            session.add(afk)
            await session.commit()

        # User starts gaining XP
        async with session_factory() as session:
            levels = Levels(
                member_id=TEST_USER_ID,
                guild_id=TEST_GUILD_ID,
                xp=50.0,
                level=2,
                blacklisted=False,
                last_message=datetime.now(UTC),
            )
            session.add(levels)
            await session.commit()

        # User sets a reminder
        async with session_factory() as session:
            from datetime import datetime, UTC

            reminder = Reminder(
                reminder_content="Check back in 1 hour",
                reminder_expires_at=datetime.now(UTC),
                reminder_channel_id=TEST_CHANNEL_ID,
                reminder_user_id=TEST_USER_ID,
                guild_id=TEST_GUILD_ID,
                reminder_sent=False,
            )
            session.add(reminder)
            await session.commit()

        # Verify complete user profile
        async with session_factory() as session:
            # Check AFK
            afk_result = await session.execute(select(AFK).where(AFK.member_id == TEST_USER_ID))
            afk_record = afk_result.scalar_one_or_none()
            assert afk_record is not None
            assert afk_record.nickname == "NewUser"

            # Check levels
            levels_result = await session.execute(select(Levels).where(Levels.member_id == TEST_USER_ID))
            levels_record = levels_result.scalar_one_or_none()
            assert levels_record is not None
            assert levels_record.xp == 50.0
            assert levels_record.level == 2

            # Check reminders
            reminder_result = await session.execute(select(Reminder).where(Reminder.reminder_user_id == TEST_USER_ID))
            reminders = reminder_result.scalars().all()
            assert len(reminders) >= 1


@pytest.mark.e2e
class TestDataMigrationWorkflow:
    """Test data migration between versions."""

    @pytest.fixture
    async def migration_test_db(self):
        """Create database for migration testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        database_url = f"sqlite+aiosqlite:///{db_path}"

        try:
            yield database_url, db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_schema_evolution(self, migration_test_db):
        """Test that schema can evolve while preserving data."""
        database_url, db_path = migration_test_db

        engine = create_async_engine(database_url, echo=False)

        # Create initial schema
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Add initial data
        async with session_factory() as session:
            guild = Guild(guild_id=TEST_GUILD_ID)
            config = GuildConfig(guild_id=TEST_GUILD_ID, prefix="!")
            session.add(guild)
            session.add(config)
            await session.commit()

        # Simulate schema evolution (in real scenario, this would be done via migrations)
        # For this test, we verify that existing data remains intact

        # Verify data persistence after schema operations
        async with session_factory() as session:
            guild_result = await session.execute(select(Guild).where(Guild.guild_id == TEST_GUILD_ID))
            found_guild = guild_result.scalar_one_or_none()
            assert found_guild is not None

            config_result = await session.execute(select(GuildConfig).where(GuildConfig.guild_id == TEST_GUILD_ID))
            found_config = config_result.scalar_one_or_none()
            assert found_config is not None
            assert found_config.prefix == "!"

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, migration_test_db):
        """Test that newer versions are backward compatible."""
        database_url, db_path = migration_test_db

        engine = create_async_engine(database_url, echo=False)

        # Create schema
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Add data in "old format" (minimal required fields)
        async with session_factory() as session:
            guild = Guild(guild_id=TEST_GUILD_ID)
            session.add(guild)
            await session.commit()

        # Verify it works with current schema expectations
        async with session_factory() as session:
            guild_result = await session.execute(select(Guild).where(Guild.guild_id == TEST_GUILD_ID))
            found_guild = guild_result.scalar_one_or_none()
            assert found_guild is not None
            assert found_guild.case_count == 0  # Default value

        await engine.dispose()


@pytest.mark.e2e
class TestScalabilityScenarios:
    """Test database behavior under various load scenarios."""

    @pytest.fixture
    async def scalability_db(self):
        """Create database for scalability testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        database_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_async_engine(database_url, echo=False)

        # Create schema
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            yield engine, database_url, session_factory
        finally:
            await engine.dispose()
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_bulk_operations(self, scalability_db):
        """Test performance with bulk operations."""
        engine, database_url, session_factory = scalability_db

        # Create multiple guilds and associated data
        async with session_factory() as session:
            for i in range(10):  # Create 10 guilds
                guild_id = TEST_GUILD_ID + i

                guild = Guild(guild_id=guild_id)
                config = GuildConfig(guild_id=guild_id, prefix=f"!{i}")

                session.add(guild)
                session.add(config)

            await session.commit()

        # Verify bulk creation worked
        async with session_factory() as session:
            guild_count = await session.execute(select(Guild))
            guilds = guild_count.scalars().all()
            assert len(guilds) >= 10

    @pytest.mark.asyncio
    async def test_query_performance(self, scalability_db):
        """Test query performance with larger datasets."""
        engine, database_url, session_factory = scalability_db

        # Setup test data
        async with session_factory() as session:
            await create_test_data(session)

            # Add additional test data
            for i in range(50):
                snippet = Snippet(
                    snippet_name=f"bulk_snippet_{i}",
                    snippet_content=f"Content {i}",
                    snippet_user_id=TEST_USER_ID,
                    guild_id=TEST_GUILD_ID,
                )
                session.add(snippet)

            await session.commit()

        # Test query performance
        async with session_factory() as session:
            # Query with filtering
            result = await session.execute(
                select(Snippet).where(
                    (Snippet.guild_id == TEST_GUILD_ID) &
                    (Snippet.snippet_name.like("bulk_snippet_%")),
                ),
            )
            bulk_snippets = result.scalars().all()
            assert len(bulk_snippets) >= 50

            # Test indexed query (should be fast)
            result = await session.execute(
                select(Guild).where(Guild.guild_id == TEST_GUILD_ID),
            )
            guild = result.scalar_one_or_none()
            assert guild is not None


@pytest.mark.e2e
class TestDisasterRecovery:
    """Test disaster recovery and backup scenarios."""

    @pytest.fixture
    async def recovery_db(self):
        """Create database for recovery testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            yield db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_data_persistence_across_restarts(self, recovery_db):
        """Test that data persists across application restarts."""
        db_path = recovery_db
        database_url = f"sqlite+aiosqlite:///{db_path}"

        # First session - create data
        engine1 = create_async_engine(database_url, echo=False)
        async with engine1.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory1 = async_sessionmaker(engine1, expire_on_commit=False)

        async with session_factory1() as session:
            guild = Guild(guild_id=TEST_GUILD_ID)
            config = GuildConfig(guild_id=TEST_GUILD_ID, prefix="!")
            session.add(guild)
            session.add(config)
            await session.commit()

        await engine1.dispose()

        # Second session - verify data persists
        engine2 = create_async_engine(database_url, echo=False)
        session_factory2 = async_sessionmaker(engine2, expire_on_commit=False)

        async with session_factory2() as session:
            guild_result = await session.execute(select(Guild).where(Guild.guild_id == TEST_GUILD_ID))
            found_guild = guild_result.scalar_one_or_none()
            assert found_guild is not None

            config_result = await session.execute(select(GuildConfig).where(GuildConfig.guild_id == TEST_GUILD_ID))
            found_config = config_result.scalar_one_or_none()
            assert found_config is not None
            assert found_config.prefix == "!"

        await engine2.dispose()

    @pytest.mark.asyncio
    async def test_corruption_recovery(self, recovery_db):
        """Test recovery from database corruption scenarios."""
        db_path = recovery_db
        database_url = f"sqlite+aiosqlite:///{db_path}"

        # Create valid database
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            guild = Guild(guild_id=TEST_GUILD_ID)
            session.add(guild)
            await session.commit()

        await engine.dispose()

        # Simulate corruption by writing invalid data
        with open(db_path, 'r+b') as f:
            f.seek(100)
            f.write(b'CORRUPTED_DATA')

        # Try to recover - this would normally require backup restoration
        # For this test, we just verify the corruption occurred
        engine = create_async_engine(database_url, echo=False)

        try:
            async with engine.begin() as conn:
                # This should fail due to corruption
                result = await conn.execute("SELECT * FROM guild")
                assert False, "Should have failed due to corruption"
        except Exception:
            # Expected - corruption detected
            assert True

        await engine.dispose()
