"""
🚀 Professional Test Configuration - Hybrid Architecture

Based on py-pglite examples and production patterns, this provides:
- UNIT TESTS: Fast sync SQLModel + py-pglite (zero-config PostgreSQL)
- INTEGRATION TESTS: Async SQLModel + real PostgreSQL (production testing)
- SHARED MODELS: Same SQLModel definitions work with both approaches

Key Features:
- Module-scoped py-pglite manager for performance
- Function-scoped sessions with clean database isolation
- Automatic SQLModel table creation and cleanup
- Support for both sync unit tests and async integration tests
- Proper test categorization and separation
"""

import os
import tempfile
import time
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session

from py_pglite.config import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager
from tux.database.service import DatabaseService


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest environment for hybrid testing."""
    os.environ.setdefault("ENV", "test")
    # Set test database URL for integration tests
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")


# ============================================================================
# UNIT TEST FIXTURES - Sync SQLModel + py-pglite
# ============================================================================

@pytest.fixture(scope="module")
def pglite_manager() -> Generator[SQLAlchemyPGliteManager]:
    """
    Module-scoped PGlite manager for fast unit testing.

    Following py-pglite example patterns for optimal performance:
    - Unique socket directory per test module
    - Single manager instance across all tests in module
    - Proper startup/shutdown lifecycle
    """
    config = PGliteConfig()

    # Create unique socket directory for isolation (py-pglite pattern)
    socket_dir = Path(tempfile.gettempdir()) / f"tux-test-{uuid.uuid4().hex[:8]}"
    socket_dir.mkdir(mode=0o700, exist_ok=True)
    config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    manager = SQLAlchemyPGliteManager(config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="module")
def pglite_engine(pglite_manager: SQLAlchemyPGliteManager) -> Engine:
    """
    Module-scoped SQLAlchemy engine optimized for py-pglite.

    Configuration based on py-pglite examples:
    - StaticPool for single persistent connection
    - Optimized connection args for Unix sockets
    - Disabled features that don't work with py-pglite
    """
    return pglite_manager.get_engine(
        poolclass=StaticPool,           # Single persistent connection
        pool_pre_ping=False,            # Disable for Unix sockets
        pool_recycle=3600,              # Longer recycle for testing
        echo=False,                     # Disable SQL logging in tests
        connect_args={
            "application_name": "tux-tests",
            "connect_timeout": 30,
            "sslmode": "disable",
        },
    )


@pytest.fixture(scope="function")
def db_session(pglite_engine: Engine) -> Generator[Session]:
    """
    Enhanced function-scoped SQLModel session with advanced py-pglite patterns.

    Features from py-pglite examples:
    - Advanced cleanup with retry logic and foreign key management
    - Bulk truncate operations for performance
    - Sequence reset for predictable ID generation
    - Error recovery patterns
    """
    # Advanced database cleanup with retry logic (py-pglite pattern)
    retry_count = 3
    for attempt in range(retry_count):
        try:
            with pglite_engine.connect() as conn:
                # Get all table names
                result = conn.execute(
                    text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    AND table_name != 'alembic_version'
                    ORDER BY table_name
                """),
                )

                table_names = [row[0] for row in result.fetchall()]

                if table_names:
                    # Disable foreign key checks for faster cleanup
                    conn.execute(text("SET session_replication_role = replica;"))

                    # Bulk truncate with CASCADE (py-pglite performance pattern)
                    truncate_sql = "TRUNCATE TABLE " + ", ".join(f'"{name}"' for name in table_names) + " RESTART IDENTITY CASCADE;"
                    conn.execute(text(truncate_sql))

                    # Reset sequences for predictable test IDs
                    for table_name in table_names:
                        try:
                            conn.execute(
                                text(f"""
                                SELECT setval(pg_get_serial_sequence('"{table_name}"', column_name), 1, false)
                                FROM information_schema.columns
                                WHERE table_name = '{table_name}'
                                AND column_default LIKE 'nextval%'
                            """),
                            )
                        except Exception:
                            # Some tables might not have sequences
                            pass

                    # Re-enable foreign key checks
                    conn.execute(text("SET session_replication_role = DEFAULT;"))
                    conn.commit()
                break  # Success, exit retry loop
        except Exception as e:
            if attempt == retry_count - 1:
                logger.warning(f"Database cleanup failed after all retries: {e}")
            else:
                time.sleep(0.1 * (attempt + 1))  # Brief exponential backoff

    # Create fresh tables with optimized settings
    SQLModel.metadata.create_all(pglite_engine, checkfirst=True)

    # Create session with enhanced configuration
    session = Session(
        pglite_engine,
        expire_on_commit=False,  # Keep objects accessible after commit
    )

    try:
        yield session
    finally:
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")


# ============================================================================
# INTEGRATION TEST FIXTURES - Async SQLModel + Real PostgreSQL
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_db_service() -> AsyncGenerator[DatabaseService]:
    """
    Async DatabaseService for integration testing with real PostgreSQL.

    Use this fixture for:
    - Integration tests that need full async architecture
    - Tests requiring real PostgreSQL features
    - End-to-end testing scenarios

    Note: Requires actual PostgreSQL database to be available
    """
    service = DatabaseService(echo=False)

    try:
        # Connect to test database (requires real PostgreSQL)
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
        await service.connect(database_url=database_url)
        await service.create_tables()

        yield service

    except Exception as e:
        # If PostgreSQL not available, skip integration tests
        pytest.skip(f"PostgreSQL not available for integration tests: {e}")
    finally:
        try:
            await service.disconnect()
        except:
            pass


@pytest_asyncio.fixture(scope="function")
async def disconnected_async_db_service() -> DatabaseService:
    """Disconnected DatabaseService for testing connection scenarios."""
    return DatabaseService(echo=False)


# ============================================================================
# ALEMBIC FIXTURES
# ============================================================================

@pytest.fixture
def alembic_engine(pglite_engine: Engine) -> Engine:
    """Provide test engine for pytest-alembic using py-pglite."""
    return pglite_engine


@pytest.fixture
def alembic_config():
    """Configure pytest-alembic with optimized settings."""
    from pytest_alembic.config import Config

    # Return pytest-alembic Config with our specific options
    yield Config(
        config_options={
            "file": "alembic.ini",
            # Enable advanced autogeneration features for better testing
            "compare_type": True,
            "compare_server_default": True,
        },
    )

    # Clean up any test revision files created during testing
    from pathlib import Path
    versions_dir = Path("src/tux/database/migrations/versions")
    if versions_dir.exists():
        for test_file in versions_dir.glob("*test_revision.py"):
            try:
                test_file.unlink()
            except OSError:
                pass  # Ignore cleanup errors


# ============================================================================
# IMPORT DATABASE FIXTURES
# ============================================================================

# Import all database fixtures to make them available
from .fixtures.database_fixtures import *  # type: ignore[import-untyped]


# ============================================================================
# INTEGRATION TEST FIXTURES - Real Database with Reset Logic
# ============================================================================

@pytest.fixture(scope="function")
async def integration_db_service() -> AsyncGenerator[DatabaseService]:
    """
    Function-scoped database service for integration tests.

    Provides a real async database connection with proper setup and cleanup
    for each test. The database is reset to ensure test isolation.
    """
    service = DatabaseService(echo=False)

    try:
        await service.connect()

        # Initial setup - full schema reset
        setup_success = await service.setup_test_database(run_migrations=False)
        if not setup_success:
            pytest.skip("Failed to set up test database - integration tests disabled")

        logger.info("Integration test database session started")
        yield service

    except Exception as e:
        logger.error(f"Failed to connect to integration database: {e}")
        pytest.skip(f"Integration database unavailable: {e}")

    finally:
        try:
            await service.disconnect()
            logger.info("Integration test database session ended")
        except Exception as e:
            logger.warning(f"Error disconnecting from integration database: {e}")


@pytest.fixture(scope="function")
async def clean_db_service(integration_db_service: DatabaseService) -> AsyncGenerator[DatabaseService]:
    """
    Function-scoped database service with automatic cleanup.

    Each test gets a clean database state. Fast data-only reset between tests
    while preserving schema structure for optimal performance.
    """
    # Clean database before test
    reset_success = await integration_db_service.reset_database_for_tests(preserve_schema=True)
    if not reset_success:
        pytest.fail("Failed to reset database before test")

    # Reset stats for clean monitoring
    await integration_db_service.reset_database_stats()

    logger.debug("Database reset completed for test")
    yield integration_db_service

    # Verify cleanup after test (optional, for debugging)
    try:
        counts = await integration_db_service.get_table_row_counts()
        if any(count > 0 for count in counts.values()):
            logger.debug(f"Test left data in database: {counts}")
    except Exception:
        # Ignore debug verification errors during teardown
        pass


@pytest.fixture(scope="function")
async def fresh_db_service(integration_db_service: DatabaseService) -> AsyncGenerator[DatabaseService]:
    """
    Function-scoped database service with full schema reset.

    For tests that need completely fresh schema (migrations, schema changes, etc.).
    Slower but provides completely clean slate.
    """
    # Full schema reset before test
    setup_success = await integration_db_service.setup_test_database(run_migrations=False)
    if not setup_success:
        pytest.fail("Failed to setup fresh database for test")

    logger.debug("Fresh database setup completed for test")
    yield integration_db_service


@pytest.fixture(scope="function")
async def migrated_db_service(integration_db_service: DatabaseService) -> AsyncGenerator[DatabaseService]:
    """
    Function-scoped database service with Alembic migrations.

    For tests that need to verify migration behavior or test against
    the exact production schema structure.
    """
    # Full schema reset with migrations
    setup_success = await integration_db_service.setup_test_database(run_migrations=True)
    if not setup_success:
        pytest.fail("Failed to setup database with migrations for test")

    logger.debug("Migrated database setup completed for test")
    yield integration_db_service


# Updated controller fixtures with database reset
@pytest.fixture
async def integration_guild_controller(clean_db_service: DatabaseService):
    """Guild controller with clean database for integration tests."""
    from tux.database.controllers.guild import GuildController
    return GuildController(clean_db_service)


@pytest.fixture
async def integration_guild_config_controller(clean_db_service: DatabaseService):
    """GuildConfig controller with clean database for integration tests."""
    from tux.database.controllers.guild_config import GuildConfigController
    return GuildConfigController(clean_db_service)


# ============================================================================
# ADVANCED TESTING FIXTURES - Inspired by py-pglite Examples
# ============================================================================

@pytest.fixture(scope="function")
def benchmark_db_session(pglite_engine: Engine) -> Generator[Session]:
    """
    High-performance database session for benchmarking tests.

    Based on py-pglite benchmark patterns with optimized configuration.
    """
    # Optimized cleanup for performance testing
    with pglite_engine.connect() as conn:
        conn.execute(text("SET synchronous_commit = OFF;"))  # Speed up writes
        conn.execute(text("SET fsync = OFF;"))  # Disable disk sync for tests
        conn.execute(text("SET full_page_writes = OFF;"))  # Reduce WAL overhead
        conn.commit()

    SQLModel.metadata.create_all(pglite_engine, checkfirst=True)
    session = Session(pglite_engine, expire_on_commit=False)

    try:
        yield session
    finally:
        session.close()
        # Reset to safe defaults
        with pglite_engine.connect() as conn:
            conn.execute(text("SET synchronous_commit = ON;"))
            conn.execute(text("SET fsync = ON;"))
            conn.execute(text("SET full_page_writes = ON;"))
            conn.commit()


@pytest.fixture(scope="function")
def transactional_db_session(pglite_engine: Engine) -> Generator[Session]:
    """
    Session that automatically rolls back all changes after each test.

    Perfect for tests that need isolation without cleanup overhead.
    Based on py-pglite transactional testing patterns.
    """
    SQLModel.metadata.create_all(pglite_engine, checkfirst=True)

    connection = pglite_engine.connect()
    transaction = connection.begin()
    session = Session(connection, expire_on_commit=False)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def db_session_with_explain(pglite_engine: Engine) -> Generator[tuple[Session, Any]]:
    """
    Session that provides query execution plan analysis.

    Returns tuple of (session, explain_analyzer) for performance debugging.
    """
    SQLModel.metadata.create_all(pglite_engine, checkfirst=True)
    session = Session(pglite_engine, expire_on_commit=False)

    class ExplainAnalyzer:
        def __init__(self, session: Session):
            self.session = session

        async def explain_query(self, stmt: Any) -> str:
            """Get execution plan for a query."""
            explain_stmt = text(f"EXPLAIN (ANALYZE, BUFFERS) {stmt}")
            result = self.session.execute(explain_stmt)
            return "\n".join([row[0] for row in result.fetchall()])

        async def explain_query_json(self, stmt: Any) -> dict:
            """Get execution plan as JSON."""
            explain_stmt = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {stmt}")
            result = self.session.execute(explain_stmt)
            import json
            return json.loads(result.scalar())

    try:
        yield session, ExplainAnalyzer(session)
    finally:
        session.close()


@pytest.fixture
def database_metrics_collector(pglite_engine: Engine):
    """
    Collect database performance metrics during test execution.

    Based on py-pglite monitoring patterns.
    """
    class MetricsCollector:
        def __init__(self, engine: Engine):
            self.engine = engine
            self.metrics = {}

        def collect_table_stats(self) -> dict[str, Any]:
            """Collect table statistics."""
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                    SELECT
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch
                    FROM pg_stat_user_tables
                    ORDER BY tablename
                """),
                )
                return [dict(row._mapping) for row in result.fetchall()]

        def collect_index_stats(self) -> dict[str, Any]:
            """Collect index usage statistics."""
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan as scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    ORDER BY tablename, indexname
                """),
                )
                return [dict(row._mapping) for row in result.fetchall()]

        def reset_stats(self):
            """Reset statistics counters."""
            with self.engine.connect() as conn:
                conn.execute(text("SELECT pg_stat_reset();"))
                conn.commit()

    collector = MetricsCollector(pglite_engine)
    collector.reset_stats()  # Start with clean metrics
    yield collector


# ============================================================================
# TEST MARKERS
# ============================================================================

# Add custom markers for test categorization
pytest_plugins = []

def pytest_collection_modifyitems(config, items):
    """Add markers based on test names and fixture usage."""
    for item in items:
        # Mark tests using async fixtures as integration tests
        if any(fixture in item.fixturenames for fixture in ['async_db_service']):
            item.add_marker(pytest.mark.integration)

        # Mark tests using sync fixtures as unit tests
        elif any(fixture in item.fixturenames for fixture in ['db_session', 'pglite_engine']):
            item.add_marker(pytest.mark.unit)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests (requires PostgreSQL)",
    )
    parser.addoption(
        "--unit-only",
        action="store_true",
        default=False,
        help="run only unit tests (py-pglite)",
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (uses py-pglite)")
    config.addinivalue_line("markers", "integration: mark test as an integration test (uses PostgreSQL)")


def pytest_runtest_setup(item):
    """Skip tests based on command line options."""
    if item.config.getoption("--unit-only"):
        if "integration" in [mark.name for mark in item.iter_markers()]:
            pytest.skip("skipping integration test in unit-only mode")

    if not item.config.getoption("--integration"):
        if "integration" in [mark.name for mark in item.iter_markers()]:
            pytest.skip("use --integration to run integration tests")
