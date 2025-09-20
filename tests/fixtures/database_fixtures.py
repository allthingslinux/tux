"""Database-related test fixtures."""

import pytest
from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from loguru import logger

from tux.database.controllers import GuildConfigController, GuildController
from tux.database.service import DatabaseService


@pytest.fixture(scope="session")
async def pglite_async_manager():
    """Session-scoped PGlite async manager - shared across tests."""
    logger.info("🔧 Creating PGlite async manager")

    manager = SQLAlchemyAsyncPGliteManager()
    try:
        manager.start()
        yield manager
    finally:
        logger.info("🧹 Cleaning up PGlite async manager")
        try:
            manager.stop()
        except Exception as e:
            logger.warning(f"Error stopping PGlite manager: {e}")
        logger.info("✅ PGlite async manager cleanup complete")


@pytest.fixture(scope="function")
async def pglite_engine(pglite_async_manager):
    """Function-scoped async engine with fresh schema per test."""
    logger.info("🔧 Creating async engine from PGlite async manager")

    engine = pglite_async_manager.get_engine()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Clean up tables after each test
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    except Exception as e:
        logger.warning(f"Error cleaning up tables: {e}")

    logger.info("🧹 Engine cleanup complete")


@pytest.fixture(scope="function")
async def db_service(pglite_engine):
    """DatabaseService with fresh database per test."""
    logger.info("🔧 Creating DatabaseService")

    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    service._engine = pglite_engine
    service._session_factory = async_sessionmaker(
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service
    logger.info("🧹 DatabaseService cleanup complete")


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


@pytest.fixture(scope="function")
async def db_session(db_service: DatabaseService):
    """Database session for direct database operations."""
    logger.info("🔧 Creating database session")
    async with db_service.session() as session:
        yield session
    logger.info("🧹 Database session cleanup complete")


@pytest.fixture(scope="function")
async def disconnected_async_db_service():
    """Database service that's not connected for testing error scenarios."""
    logger.info("🔧 Creating disconnected database service")
    from tux.database.service import AsyncDatabaseService
    service = AsyncDatabaseService(echo=False)
    # Don't connect - leave it disconnected for error testing
    yield service
    logger.info("🧹 Disconnected database service cleanup complete")
