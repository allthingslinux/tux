"""
Clean Test Configuration - Self-Contained Testing

This provides clean, maintainable test fixtures using the async-agnostic
DatabaseService architecture with self-contained databases:

- ALL TESTS: py-pglite (self-contained PostgreSQL in-memory)
- No external dependencies required - tests run anywhere
- Clean separation of concerns with proper dependency injection

Key Features:
- Simple, clean fixtures using DatabaseServiceFactory
- Self-contained testing with py-pglite
- Full PostgreSQL compatibility
- Module-scoped managers with function-scoped sessions for optimal performance
- Unique socket paths to prevent conflicts between test modules
- Robust cleanup with retry logic
"""

import tempfile
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import pytest
from loguru import logger

from tux.database.service import DatabaseServiceABC, DatabaseServiceFactory, DatabaseMode
from tux.database.models.models import Guild, GuildConfig
from tests.fixtures.database_fixtures import TEST_GUILD_ID, TEST_CHANNEL_ID

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers and settings."""
    # Note: Integration tests now use py-pglite (self-contained)
    # No need to set DATABASE_URL - fixtures handle connection setup

    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test (uses py-pglite)")
    config.addinivalue_line("markers", "integration: mark test as an integration test (uses py-pglite)")
    config.addinivalue_line("markers", "slow: mark test as slow (>5 seconds)")

    # Filter expected warnings to reduce noise in test output
    config.addinivalue_line(
        "filterwarnings",
        "ignore:New instance .* with identity key .* conflicts with persistent instance:sqlalchemy.exc.SAWarning",
    )


# ============================================================================
# DATABASE FIXTURES - Self-contained py-pglite (Optimized!)
# ============================================================================

@pytest.fixture
def db_service() -> DatabaseServiceABC:
    """Function-scoped async database service using py-pglite."""
    return DatabaseServiceFactory.create(DatabaseMode.ASYNC, echo=False)


@pytest.fixture
async def fresh_db(db_service: DatabaseServiceABC) -> AsyncGenerator[DatabaseServiceABC]:
    """Function-scoped fresh test database with optimized py-pglite setup.

    PERFORMANCE OPTIMIZATION: Creates unique work directories but reuses
    node_modules from a shared location. Creates unique socket paths for isolation.
    """
    logger.info("🔧 Setting up optimized fresh database")

    # Create unique configuration for this test to prevent conflicts
    from py_pglite import PGliteManager, PGliteConfig

    config = PGliteConfig()

    # Create unique work directory for this test to prevent conflicts
    unique_work_dir = Path(tempfile.gettempdir()) / f"tux_pglite_work_{uuid.uuid4().hex[:8]}"
    unique_work_dir.mkdir(mode=0o700, exist_ok=True)
    config.work_dir = unique_work_dir

    # Increase timeout for npm install reliability
    config.timeout = 120  # 2 minutes for npm install

    # Create unique socket directory for this test to prevent conflicts
    socket_dir = (
        Path(tempfile.gettempdir()) / f"tux-pglite-{uuid.uuid4().hex[:8]}"
    )
    socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
    config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    logger.info(f"📂 Socket path: {config.socket_path}")
    logger.info(f"📁 Work dir: {config.work_dir}")

    manager = PGliteManager(config)

    try:
        logger.info("⚡ Starting PGlite (npm install should be cached!)")
        manager.start()
        logger.info("✅ PGlite ready!")

        # Get connection string from the manager
        pglite_url = manager.get_connection_string()

        await db_service.connect(pglite_url)
        logger.info("✅ Database connected")

        # Initial database schema setup
        await _reset_database_schema(db_service)
        logger.info("🏗️ Schema setup complete")

        yield db_service

    except Exception as e:
        logger.error(f"❌ Failed to setup database: {e}")
        raise
    finally:
        try:
            await db_service.disconnect()
            logger.info("🔌 Database disconnected")
        except Exception as e:
            logger.warning(f"⚠️ Error disconnecting database: {e}")
        finally:
            try:
                manager.stop()
                logger.info("🛑 PGlite stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping PGlite: {e}")


@pytest.fixture
async def db_session(fresh_db: DatabaseServiceABC) -> AsyncGenerator[Any]:
    """Function-scoped database session with per-test data cleanup.

    PERFORMANCE: Uses fast truncation instead of full schema reset.
    """
    logger.debug("⚡ Setting up database session with fast cleanup...")

    try:
        # Fast per-test cleanup: just truncate data, don't recreate schema
        await _fast_cleanup_database(fresh_db)

        async with fresh_db.session() as session:
            logger.debug("✅ Database session ready")
            yield session

    except Exception as e:
        logger.error(f"❌ Failed to setup database session: {e}")
        raise
    finally:
        logger.debug("🧹 Session cleanup complete")


# Alias for backward compatibility
@pytest.fixture
def integration_db_service(db_service: DatabaseServiceABC) -> DatabaseServiceABC:
    """Alias for db_service for backward compatibility."""
    return db_service


@pytest.fixture
async def fresh_integration_db(fresh_db: DatabaseServiceABC) -> AsyncGenerator[DatabaseServiceABC]:
    """Alias for fresh_db for backward compatibility."""
    yield fresh_db


async def _fast_cleanup_database(service: DatabaseServiceABC) -> None:
    """Fast per-test cleanup: truncate data without recreating schema.

    This is MUCH faster than full schema reset - just clears data while
    keeping the table structure intact. Perfect for session-scoped databases.
    """
    from sqlalchemy import text

    logger.debug("🧹 Starting fast database cleanup (truncate only)...")

    try:
        async with service.session() as session:
            # Get all table names from information_schema
            result = await session.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """),
            )

            table_names = [row[0] for row in result]
            logger.debug(f"Found tables to truncate: {table_names}")

            if table_names:
                # Disable foreign key checks for faster cleanup
                await session.execute(text("SET session_replication_role = replica;"))

                # Truncate all tables (fast data cleanup)
                for table_name in table_names:
                    await session.execute(
                        text(
                            f'TRUNCATE TABLE "{table_name}" '
                            "RESTART IDENTITY CASCADE;",
                        ),
                    )

                # Re-enable foreign key checks
                await session.execute(text("SET session_replication_role = DEFAULT;"))

                # Commit the cleanup
                await session.commit()
                logger.debug("✅ Fast database cleanup completed")
            else:
                logger.debug("ℹ️ No tables found to clean")

    except Exception as e:
        logger.error(f"❌ Fast database cleanup failed: {e}")
        raise


async def _reset_database_schema(service: DatabaseServiceABC) -> None:
    """Full database schema reset with retry logic and robust cleanup.

    Used only once per session for initial setup. For per-test cleanup,
    use _fast_cleanup_database() instead - it's much faster!
    """
    from sqlalchemy import text

    logger.info("🏗️ Starting full database schema reset (session setup)...")

    # Retry logic for robust cleanup
    retry_count = 3
    for attempt in range(retry_count):
        try:
            async with service.session() as session:
                # Clean up data before schema reset with retry logic
                logger.info("Starting database cleanup before schema reset...")

                # Get all table names from information_schema
                result = await session.execute(
                    text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """),
                )

                table_names = [row[0] for row in result]
                logger.info(f"Found tables to clean: {table_names}")

                if table_names:
                    # Disable foreign key checks for faster cleanup
                    await session.execute(text("SET session_replication_role = replica;"))

                    # Truncate all tables
                    for table_name in table_names:
                        logger.info(f"Truncating table: {table_name}")
                        await session.execute(
                            text(
                                f'TRUNCATE TABLE "{table_name}" '
                                "RESTART IDENTITY CASCADE;",
                            ),
                        )

                    # Re-enable foreign key checks
                    await session.execute(text("SET session_replication_role = DEFAULT;"))

                    # Commit the cleanup
                    await session.commit()
                    logger.info("Database cleanup completed successfully")
                else:
                    logger.info("No tables found to clean")

                # Now drop and recreate schema
                # Drop all tables first
                result = await session.execute(
                    text("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                """),
                )
                tables = result.fetchall()

                for (table_name,) in tables:
                    await session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))

                # Drop all enum types
                result = await session.execute(
                    text("""
                    SELECT typname FROM pg_type
                    WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                """),
                )
                enums = result.fetchall()

                for (enum_name,) in enums:
                    try:
                        await session.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
                    except Exception as e:
                        logger.warning(f"Could not drop enum {enum_name}: {e}")
                        # Some enums might be referenced, continue anyway

                await session.commit()

                # Create tables using SQLModel with retry logic
                from sqlmodel import SQLModel

                if service.engine:
                    for create_attempt in range(3):
                        try:
                            async with service.engine.begin() as conn:
                                await conn.run_sync(SQLModel.metadata.create_all, checkfirst=False)
                            break
                        except Exception as e:
                            logger.warning(f"Table creation attempt {create_attempt + 1} failed: {e}")
                            if create_attempt == 2:
                                raise
                            time.sleep(0.5)

                logger.info("✅ Database schema reset complete")
                return  # Success, exit retry loop

        except Exception as e:
            logger.info(f"Database cleanup/schema reset attempt {attempt + 1} failed: {e}")
            if attempt == retry_count - 1:
                logger.error("Database cleanup/schema reset failed after all retries")
                raise
            else:
                time.sleep(0.5)  # Brief pause before retry





# ============================================================================
# ADDITIONAL FIXTURES FOR EXISTING TESTS
# ============================================================================

@pytest.fixture
async def clean_db_service(fresh_db: DatabaseServiceABC) -> AsyncGenerator[DatabaseServiceABC]:
    """Clean database service."""
    yield fresh_db


@pytest.fixture
def async_db_service(db_service: DatabaseServiceABC) -> DatabaseServiceABC:
    """Async database service."""
    return db_service


@pytest.fixture
def integration_guild_controller(fresh_db: DatabaseServiceABC) -> Any:
    """Guild controller for tests."""
    from tux.database.controllers.guild import GuildController
    return GuildController(fresh_db)


@pytest.fixture
def integration_guild_config_controller(fresh_db: DatabaseServiceABC) -> Any:
    """Guild config controller for tests."""
    from tux.database.controllers.guild_config import GuildConfigController
    return GuildConfigController(fresh_db)


@pytest.fixture
def disconnected_async_db_service() -> DatabaseServiceABC:
    """Disconnected async database service for testing connection scenarios."""
    return DatabaseServiceFactory.create(DatabaseMode.ASYNC, echo=False)


# =============================================================================
# MODEL SAMPLE FIXTURES - For serialization and basic model tests
# =============================================================================

@pytest.fixture
def sample_guild() -> Guild:
    """Sample Guild model instance for testing."""
    return Guild(
        guild_id=TEST_GUILD_ID,
        case_count=5,
        guild_joined_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_guild_config() -> GuildConfig:
    """Sample GuildConfig model instance for testing."""
    return GuildConfig(
        guild_id=TEST_GUILD_ID,
        prefix="!test",
        mod_log_id=TEST_CHANNEL_ID,
    )


@pytest.fixture
def multiple_guilds() -> list[Guild]:
    """List of Guild model instances for testing."""
    return [
        Guild(
            guild_id=TEST_GUILD_ID + i,
            case_count=i,
            guild_joined_at=datetime.now(UTC),
        )
        for i in range(5)
    ]


@pytest.fixture
def populated_test_database() -> dict[str, Any]:
    """Populated test database with sample data for performance testing."""
    guilds = []
    configs = []

    for i in range(10):
        guild = Guild(
            guild_id=TEST_GUILD_ID + i,
            case_count=i * 2,
            guild_joined_at=datetime.now(UTC),
        )
        config = GuildConfig(
            guild_id=TEST_GUILD_ID + i,
            prefix=f"!guild{i}",
            mod_log_id=TEST_CHANNEL_ID + i,
        )
        guilds.append(guild)
        configs.append(config)

    return {
        "guilds": [{"guild": guild, "config": config} for guild, config in zip(guilds, configs)],
        "total_guilds": len(guilds),
    }
