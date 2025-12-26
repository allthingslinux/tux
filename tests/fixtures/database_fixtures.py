"""Database-related test fixtures."""

import pytest
from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from loguru import logger

from tux.database.controllers import (
    GuildConfigController,
    GuildController,
    PermissionAssignmentController,
    PermissionCommandController,
    PermissionRankController,
)
from tux.database.service import DatabaseService


@pytest.fixture(scope="session")
async def pglite_async_manager():
    """Session-scoped PGlite async manager - shared across tests."""
    manager = SQLAlchemyAsyncPGliteManager()
    try:
        manager.start()
        # Wait for PGlite to be fully ready before yielding
        if not manager.wait_for_ready(max_retries=10, delay=0.1):
            raise RuntimeError("PGlite failed to become ready after startup")
        yield manager
    finally:
        try:
            manager.stop()
        except Exception as exc:
            logger.exception("Failed to stop PGlite manager during test teardown: {}", exc)


@pytest.fixture(scope="function")
async def pglite_engine(pglite_async_manager):
    """Function-scoped async engine with fresh schema per test."""
    engine = pglite_async_manager.get_engine()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Clean up tables after each test
    # Cleanup failures are non-fatal and should not break tests
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    except Exception as exc:
        logger.exception("Failed to clean up tables during test teardown: {}", exc)


@pytest.fixture(scope="function")
async def db_service(pglite_engine):
    """DatabaseService with fresh database per test."""
    from tux.database.service import DatabaseService
    service = DatabaseService(echo=False)

    # Manually set the engine and session factory to use our PGlite engine
    service._engine = pglite_engine  # noqa: SLF001
    service._session_factory = async_sessionmaker(  # noqa: SLF001
        pglite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield service


@pytest.fixture(scope="function")
async def guild_controller(db_service: DatabaseService) -> GuildController:
    """GuildController with fresh database per test."""
    return GuildController(db_service)


@pytest.fixture(scope="function")
async def guild_config_controller(db_service: DatabaseService) -> GuildConfigController:
    """GuildConfigController with fresh database per test."""
    return GuildConfigController(db_service)


@pytest.fixture(scope="function")
async def db_session(db_service: DatabaseService):
    """Database session for direct database operations."""
    async with db_service.session() as session:
        yield session


@pytest.fixture(scope="function")
async def disconnected_async_db_service():
    """Database service that's not connected for testing error scenarios."""
    from tux.database.service import DatabaseService
    service = DatabaseService(echo=False)
    # Don't connect - leave it disconnected for error testing
    yield service


@pytest.fixture(scope="function")
async def permission_rank_controller(db_service: DatabaseService) -> PermissionRankController:
    """PermissionRankController with fresh database per test."""
    return PermissionRankController(db_service)


@pytest.fixture(scope="function")
async def permission_assignment_controller(db_service: DatabaseService) -> PermissionAssignmentController:
    """PermissionAssignmentController with fresh database per test."""
    return PermissionAssignmentController(db_service)


@pytest.fixture(scope="function")
async def permission_command_controller(db_service: DatabaseService) -> PermissionCommandController:
    """PermissionCommandController with fresh database per test."""
    return PermissionCommandController(db_service)


@pytest.fixture(scope="function")
async def permission_system(db_service: DatabaseService):
    """PermissionSystem with fresh database per test."""
    from unittest.mock import MagicMock
    from tux.core.permission_system import PermissionSystem
    from tux.database.controllers import DatabaseCoordinator

    # Create a mock bot
    mock_bot = MagicMock()
    mock_bot.owner_ids = set()

    # Create database coordinator
    db_coordinator = DatabaseCoordinator(db_service)

    # Create PermissionSystem
    perm_system = PermissionSystem(mock_bot, db_coordinator)
    yield perm_system
