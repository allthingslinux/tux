from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from tux.utils.config import CONFIG

T = TypeVar("T")

# Error messages
CLIENT_NOT_CONNECTED = "Database client is not connected. Call connect() first."
CLIENT_ALREADY_CONNECTED = "Database client is already connected."


class DatabaseClient:
    """A singleton database client that manages the SQLModel connection.

    This class provides a centralized way to manage the database connection
    and ensures proper connection handling throughout the application lifecycle.
    """

    # Async engine for Postgres
    engine = create_async_engine(CONFIG.DATABASE_URL, echo=True, future=True)
    # Async session factory
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    def __init__(self) -> None:
        # Track whether connect() and init_db() have run
        self._connected = False
        self._registered = False

    async def connect(self) -> None:
        """Establish a test connection and initialize database tables."""
        if self._connected:
            raise RuntimeError(CLIENT_ALREADY_CONNECTED)
        # Create tables and test engine
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        self._connected = True
        self._registered = True

    async def disconnect(self) -> None:
        """Dispose the engine and reset connection state."""
        await self.engine.dispose()
        self._connected = False
        self._registered = False

    def is_connected(self) -> bool:
        """Return True if connect() has been successfully called."""
        return self._connected

    def is_registered(self) -> bool:
        """Return True if tables have been created."""
        return self._registered

    async def init_db(self) -> None:
        """
        Create all tables defined in SQLModel metadata.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    def get_session(self) -> AsyncSession:
        """
        Return a new AsyncSession. Use with `async with` context or close manually.
        """
        return self.SessionLocal()


# Global database client instance
db = DatabaseClient()
