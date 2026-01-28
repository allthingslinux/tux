"""Cache service for Valkey (Redis-compatible) connection management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from valkey.asyncio import Valkey
from valkey.backoff import ExponentialBackoff
from valkey.exceptions import (
    BusyLoadingError,
)
from valkey.exceptions import (
    ConnectionError as ValkeyConnectionError,
)
from valkey.exceptions import (
    TimeoutError as ValkeyTimeoutError,
)
from valkey.retry import Retry

from tux.shared.config import CONFIG

if TYPE_CHECKING:
    from valkey.asyncio import Valkey as ValkeyClient

__all__ = ["CacheService"]

# Socket connect timeout (seconds) so startup does not hang if Valkey is down
SOCKET_CONNECT_TIMEOUT = 5.0
# Retry count and backoff for transient failures (e.g. Valkey still loading)
RETRY_COUNT = 3


class CacheService:
    """
    Async cache service for Valkey (Redis-compatible) operations.

    Provides a single connection pool and client for all cache operations.
    Optional: when VALKEY_URL is empty or connection fails, bot runs without Valkey
    and consumers fall back to in-memory caches.

    Attributes
    ----------
    _client : Valkey | None
        Async Valkey client (from valkey.asyncio). None when disconnected.
    """

    def __init__(self) -> None:
        """Initialize the cache service (no connection yet)."""
        self._client: ValkeyClient | None = None

    async def connect(self, url: str | None = None, **kwargs: Any) -> None:
        """
        Connect to Valkey using the given URL or CONFIG.valkey_url.

        Parameters
        ----------
        url : str | None, optional
            Valkey URL (valkey://...). If None, uses CONFIG.valkey_url.
        **kwargs : Any
            Additional arguments passed to Valkey.from_url (override URL params).
        """
        valkey_url = url or CONFIG.valkey_url
        if not valkey_url:
            logger.debug("Valkey URL not configured; cache service will not connect")
            return

        retry = Retry(ExponentialBackoff(), RETRY_COUNT)
        # Use valkey.exceptions so transient failures are retried
        retry_on_error: list[type[Exception]] = [
            BusyLoadingError,
            ValkeyConnectionError,
            ValkeyTimeoutError,
        ]

        logger.debug("Connecting to Valkey...")
        try:
            self._client = Valkey.from_url(
                valkey_url,
                decode_responses=True,
                socket_connect_timeout=SOCKET_CONNECT_TIMEOUT,
                retry=retry,
                retry_on_error=retry_on_error,
                **kwargs,
            )
            logger.success("Connected to Valkey")
        except Exception as e:
            logger.warning(f"Failed to connect to Valkey: {e}")
            self._client = None
            raise

    def is_connected(self) -> bool:
        """
        Return whether the cache service is connected to Valkey.

        Returns
        -------
        bool
            True if a client exists and is usable.
        """
        return self._client is not None

    def get_client(self) -> ValkeyClient | None:
        """
        Return the async Valkey client for cache operations.

        Returns
        -------
        ValkeyClient | None
            The Valkey client, or None if not connected.
        """
        return self._client

    async def ping(self) -> bool:
        """
        Ping Valkey to verify connectivity.

        Returns
        -------
        bool
            True if ping succeeded, False if not connected or ping failed.
        """
        if self._client is None:
            return False
        try:
            await self._client.ping()  # type: ignore[no-any-return]
        except Exception as e:
            logger.debug(f"Valkey ping failed: {e}")
            return False
        else:
            return True

    async def close(self) -> None:
        """
        Close the Valkey connection and release the pool.

        Must be called on shutdown; there is no asyncio destructor.
        Safe to call when not connected.
        """
        if self._client is None:
            return
        try:
            await self._client.aclose()
        except Exception as e:
            logger.warning(f"Error closing Valkey client: {e}")
        finally:
            self._client = None
        logger.debug("Valkey connection closed")
