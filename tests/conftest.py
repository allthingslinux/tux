"""
🧪 Clean Test Configuration - Simplified Architecture

This conftest.py follows the clean slate approach:
- Function-scoped fixtures (not session-scoped)
- Simple py-pglite integration
- No complex schema management
- Follows py-pglite examples exactly
"""

import logging
import pytest
import pytest_asyncio
import subprocess
import atexit
from typing import Any

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager
from sqlmodel import SQLModel

from tux.database.service import DatabaseService
from tux.database.controllers import GuildController, GuildConfigController

# Test constants
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321
TEST_MODERATOR_ID = 555666777888999000

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# PGLITE PROCESS CLEANUP - Prevent process accumulation
# =============================================================================

def _cleanup_all_pglite_processes() -> None:
    """Clean up all pglite_manager.js processes.

    This function ensures all PGlite processes are terminated to prevent
    memory leaks and process accumulation during testing.
    """
    logger.info("🧹 Starting comprehensive PGlite process cleanup...")

    try:
        # Use ps command to find PGlite processes
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.warning("⚠️ Failed to get process list")
            return

        pglite_processes = []
        for line in result.stdout.split('\n'):
            if 'pglite_manager.js' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    pglite_processes.append(pid)
                    logger.debug(f"🔍 Found PGlite process: PID {pid}")

        if not pglite_processes:
            logger.info("✅ No PGlite processes found to clean up")
            return

        logger.info(f"🔧 Found {len(pglite_processes)} PGlite processes to clean up")

        # Kill all PGlite processes
        for pid in pglite_processes:
            try:
                logger.info(f"🔪 Terminating PGlite process: PID {pid}")
                subprocess.run(
                    ["kill", "-TERM", pid],
                    timeout=5,
                    check=False,
                )
                # Wait a moment for graceful shutdown
                subprocess.run(
                    ["sleep", "0.5"],
                    timeout=1,
                    check=False,
                )
                # Force kill if still running
                subprocess.run(
                    ["kill", "-KILL", pid],
                    timeout=5,
                    check=False,
                )
                logger.debug(f"✅ Successfully terminated PGlite process: PID {pid}")
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ Timeout killing process {pid}")
            except Exception as e:
                logger.warning(f"⚠️ Error killing process {pid}: {e}")

        logger.info("✅ PGlite process cleanup completed")

    except Exception as e:
        logger.error(f"❌ Error during PGlite cleanup: {e}")
        # Fallback to psutil if subprocess approach fails
        try:
            import psutil
            logger.info("🔄 Attempting fallback cleanup with psutil...")
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if proc.info["cmdline"] and any("pglite_manager.js" in cmd for cmd in proc.info["cmdline"]):
                    try:
                        logger.info(f"🔪 Fallback: Killing PGlite process PID {proc.info['pid']}")
                        proc.kill()
                        proc.wait(timeout=2)
                        logger.debug(f"✅ Fallback: Successfully killed PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    except Exception as e:
                        logger.warning(f"⚠️ Fallback: Error killing PID {proc.info['pid']}: {e}")
            logger.info("✅ Fallback cleanup completed")
        except ImportError:
            logger.warning("⚠️ psutil not available for fallback cleanup")
        except Exception as e:
            logger.error(f"❌ Fallback cleanup failed: {e}")


def _monitor_pglite_processes() -> int:
    """Monitor and count current PGlite processes.

    Returns:
        Number of PGlite processes currently running
    """
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return 0

        return sum(
            'pglite_manager.js' in line and 'grep' not in line
            for line in result.stdout.split('\n')
        )

    except Exception as e:
        logger.warning(f"⚠️ Error monitoring PGlite processes: {e}")
        return 0


# Register cleanup function to run on exit
atexit.register(_cleanup_all_pglite_processes)


# =============================================================================
# PYTEST HOOKS - Ensure cleanup happens
# =============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Clean up PGlite processes after test session finishes."""
    logger.info("🏁 Test session finished - cleaning up PGlite processes")
    _cleanup_all_pglite_processes()

    # Final verification
    final_count = _monitor_pglite_processes()
    if final_count > 0:
        logger.warning(f"⚠️ {final_count} PGlite processes still running after session cleanup")
    else:
        logger.info("✅ All PGlite processes cleaned up after test session")


def pytest_runtest_teardown(item, nextitem):
    """Clean up PGlite processes after each test."""
    # Disabled periodic cleanup to avoid interfering with running tests
    # Cleanup is now handled at fixture level and session end
    pass


# =============================================================================
# CORE DATABASE FIXTURES - Function-scoped, Simple
# =============================================================================

@pytest.fixture(scope="function")
async def pglite_async_manager():
    """Function-scoped PGlite async manager - fresh for each test."""
    # Monitor processes before starting
    initial_count = _monitor_pglite_processes()
    if initial_count > 0:
        logger.warning(f"⚠️ Found {initial_count} PGlite processes before test start - cleaning up")
        _cleanup_all_pglite_processes()

    logger.info("🔧 Creating fresh PGlite async manager")
    config = PGliteConfig(use_tcp=False, cleanup_on_exit=True)  # Use Unix socket for simplicity
    manager = SQLAlchemyAsyncPGliteManager(config)
    manager.start()

    # Verify process started
    process_count = _monitor_pglite_processes()
    logger.info(f"📊 PGlite processes after start: {process_count}")

    yield manager

    logger.info("🧹 Cleaning up PGlite async manager")
    try:
        manager.stop()
        logger.info("✅ PGlite manager stopped successfully")
    except Exception as e:
        logger.warning(f"⚠️ Error stopping PGlite manager: {e}")

    # Small delay to ensure test has fully completed
    import time
    time.sleep(0.1)

    # Force cleanup of any remaining processes
    _cleanup_all_pglite_processes()

    # Verify cleanup
    final_count = _monitor_pglite_processes()
    if final_count > 0:
        logger.warning(f"⚠️ {final_count} PGlite processes still running after cleanup")
    else:
        logger.info("✅ All PGlite processes cleaned up successfully")


@pytest.fixture(scope="function")
async def pglite_engine(pglite_async_manager):
    """Function-scoped async engine with fresh schema per test."""
    logger.info("🔧 Creating async engine from PGlite async manager")
    engine = pglite_async_manager.get_engine()

    # Create schema using py-pglite's recommended pattern
    logger.info("🔧 Creating database schema")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)

    logger.info("✅ Database schema created successfully")
    yield engine
    logger.info("🧹 Engine cleanup complete")


@pytest.fixture(scope="function")
async def db_service(pglite_engine):
    """DatabaseService with fresh database per test."""
    logger.info("🔧 Creating DatabaseService")
    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    service._engine = pglite_engine
    service._session_factory = async_sessionmaker(
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service
    logger.info("🧹 DatabaseService cleanup complete")


# =============================================================================
# CONTROLLER FIXTURES - Simple and Direct
# =============================================================================

@pytest.fixture(scope="function")
async def guild_controller(db_service: DatabaseService) -> GuildController:
    """GuildController with fresh database per test."""
    logger.info("🔧 Creating GuildController")
    return GuildController(db_service)


@pytest.fixture(scope="function")
async def guild_config_controller(db_service: DatabaseService) -> GuildConfigController:
    """GuildConfigController with fresh database per test."""
    logger.info("🔧 Creating GuildConfigController")
    return GuildConfigController(db_service)


# =============================================================================
# TEST DATA FIXTURES - Simple and Focused
# =============================================================================

@pytest.fixture(scope="function")
async def sample_guild(guild_controller: GuildController) -> Any:
    """Sample guild for testing."""
    logger.info("🔧 Creating sample guild")
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
    logger.info(f"✅ Created sample guild: {guild.guild_id}")
    return guild


@pytest.fixture(scope="function")
async def sample_guild_with_config(guild_controller: GuildController, guild_config_controller: GuildConfigController) -> dict[str, Any]:
    """Sample guild with config for testing."""
    logger.info("🔧 Creating sample guild with config")

    # Create guild
    guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

    # Create config
    config = await guild_config_controller.create_config(
        guild_id=guild.guild_id,
        prefix="!",
        mod_log_id=TEST_CHANNEL_ID,
        audit_log_id=TEST_CHANNEL_ID + 1,
        starboard_channel_id=TEST_CHANNEL_ID + 2,
    )

    logger.info(f"✅ Created guild with config: {guild.guild_id}")
    return {
        'guild': guild,
        'config': config,
        'guild_controller': guild_controller,
        'guild_config_controller': guild_config_controller,
    }


# =============================================================================
# INTEGRATION TEST FIXTURES - For complex integration scenarios
# =============================================================================

@pytest.fixture(scope="function")
async def fresh_integration_db(pglite_engine):
    """Fresh database service for integration tests."""
    logger.info("🔧 Creating fresh integration database service")
    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    service._engine = pglite_engine
    service._session_factory = async_sessionmaker(
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service
    logger.info("🧹 Fresh integration database cleanup complete")


@pytest.fixture(scope="function")
async def disconnected_async_db_service():
    """Database service that's not connected for testing error scenarios."""
    logger.info("🔧 Creating disconnected database service")
    from tux.database.service import AsyncDatabaseService
    # Don't set up engine or session factory - leave it disconnected
    yield AsyncDatabaseService(echo=False)
    logger.info("🧹 Disconnected database service cleanup complete")


@pytest.fixture(scope="function")
async def db_session(db_service: DatabaseService):
    """Database session for direct database operations."""
    logger.info("🔧 Creating database session")
    async with db_service.session() as session:
        yield session
    logger.info("🧹 Database session cleanup complete")


@pytest.fixture(scope="function")
async def fresh_db(pglite_engine):
    """Fresh database service for integration tests (alias for fresh_integration_db)."""
    logger.info("🔧 Creating fresh database service")
    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    service._engine = pglite_engine
    service._session_factory = async_sessionmaker(
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service
    logger.info("🧹 Fresh database cleanup complete")


@pytest.fixture(scope="function")
async def clean_db_service(pglite_engine):
    """Clean database service for integration tests (alias for fresh_db)."""
    logger.info("🔧 Creating clean database service")
    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    service._engine = pglite_engine
    service._session_factory = async_sessionmaker(
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service
    logger.info("🧹 Clean database cleanup complete")


@pytest.fixture(scope="function")
async def integration_db_service(pglite_engine):
    """Integration database service for integration tests (alias for fresh_integration_db)."""
    logger.info("🔧 Creating integration database service")
    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    service._engine = pglite_engine
    service._session_factory = async_sessionmaker(
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service
    logger.info("🧹 Integration database cleanup complete")


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with clean settings."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Auto-mark unit tests
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_guild_structure(guild: Any) -> bool:
    """Validate guild model structure and required fields."""
    return (
        hasattr(guild, 'guild_id') and
        hasattr(guild, 'case_count') and
        hasattr(guild, 'guild_joined_at') and
        isinstance(guild.guild_id, int) and
        isinstance(guild.case_count, int)
    )


def validate_guild_config_structure(config: Any) -> bool:
    """Validate guild config model structure and required fields."""
    return (
        hasattr(config, 'guild_id') and
        hasattr(config, 'prefix') and
        isinstance(config.guild_id, int) and
        (config.prefix is None or isinstance(config.prefix, str))
    )


def validate_relationship_integrity(guild: Any, config: Any) -> bool:
    """Validate relationship integrity between guild and config."""
    return guild.guild_id == config.guild_id


# =============================================================================
# LEGACY COMPATIBILITY - For Gradual Migration
# =============================================================================

# Keep these for any existing tests that might depend on them
@pytest.fixture(scope="function")
async def integration_guild_controller(guild_controller: GuildController) -> GuildController:
    """Legacy compatibility - same as guild_controller."""
    return guild_controller


@pytest.fixture(scope="function")
async def integration_guild_config_controller(guild_config_controller: GuildConfigController) -> GuildConfigController:
    """Legacy compatibility - same as guild_config_controller."""
    return guild_config_controller
