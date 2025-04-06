from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypeVar

from loguru import logger

from prisma import Prisma

T = TypeVar("T")

# Error messages
CLIENT_NOT_CONNECTED = "Database client is not connected. Call connect() first."
CLIENT_ALREADY_CONNECTED = "Database client is already connected."


class DatabaseClient:
    """A singleton database client that manages the Prisma connection.

    This class provides a centralized way to manage the database connection
    and ensures proper connection handling throughout the application lifecycle.
    """

    _instance = None
    _client: Prisma | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> Prisma:
        """Get the Prisma client instance.

        Returns
        -------
        Prisma
            The Prisma client instance.

        Raises
        ------
        RuntimeError
            If the client is not connected.
        """
        if self._client is None:
            raise RuntimeError(CLIENT_NOT_CONNECTED)
        return self._client

    def is_connected(self) -> bool:
        """Check if the database client is connected.

        Returns
        -------
        bool
            True if the client is connected, False otherwise.
        """
        return self._client is not None

    def is_registered(self) -> bool:
        """Check if the database client is properly registered.

        Returns
        -------
        bool
            True if the client is registered with models, False otherwise.
        """
        # Since we use auto_register=True in connect(), if connected then registered
        return self.is_connected()

    async def connect(self) -> None:
        """Connect to the database.

        This method establishes the database connection and performs
        any necessary initialization.

        Notes
        -----
        The DATABASE_URL environment variable should be set before calling
        this method, which is handled by the tux.utils.env module.
        """
        if self._client is not None:
            logger.warning(CLIENT_ALREADY_CONNECTED)
            return

        try:
            self._client = Prisma(
                log_queries=False,
                auto_register=True,
            )
            await self._client.connect()
            logger.info("Successfully connected to database.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the database.

        This method closes the database connection and performs
        any necessary cleanup.
        """
        if self._client is None:
            logger.warning("Database client is not connected.")
            return

        try:
            await self._client.disconnect()
            self._client = None
            logger.info("Successfully disconnected from database.")
        except Exception as e:
            logger.error(f"Failed to disconnect from database: {e}")
            raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None]:
        """Create a database transaction.

        This context manager ensures that database operations are atomic
        and handles rollback in case of errors.

        Yields
        ------
        None
            Control is yielded to the caller within the transaction.
        """
        if self._client is None:
            raise RuntimeError(CLIENT_NOT_CONNECTED)

        async with self._client.batch_() as _:
            try:
                yield
            except Exception as e:
                logger.error(f"Transaction failed, rolling back: {e}")
                raise

    async def batch(self) -> AsyncGenerator[None]:
        """Create a batch operation context.

        This context manager allows batching multiple write operations
        into a single database call for better performance.

        Yields
        ------
        None
            Control is yielded to the caller within the batch context.
        """
        if self._client is None:
            raise RuntimeError(CLIENT_NOT_CONNECTED)

        async with self._client.batch_() as _:
            yield


# Global database client instance
db = DatabaseClient()
