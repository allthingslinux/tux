"""Centralized HTTP client service for Tux bot.

This module provides a shared httpx.AsyncClient instance with connection pooling,
proper timeout configuration, and error handling for all HTTP requests across the bot.

Lifecycle Management
--------------------
The HTTP client follows a singleton pattern with lazy initialization:

1. **Initialization**: Module-level `http_client` instance is created on import
2. **Connection**: AsyncClient is created on first use (lazy initialization)
3. **Reuse**: All subsequent requests use the same pooled client
4. **Cleanup**: Bot calls `http_client.close()` during shutdown

Usage Examples
--------------
>>> from tux.services.http_client import http_client
>>>
>>> # GET request
>>> response = await http_client.get("https://api.example.com/data")
>>> data = response.json()
>>>
>>> # POST request with JSON
>>> response = await http_client.post(
...     "https://api.example.com/submit", json={"key": "value"}
... )
>>>
>>> # Custom timeout
>>> response = await http_client.get("https://slow-api.example.com", timeout=60.0)

Configuration
-------------
The client is pre-configured with:
- Connection pooling (max 100 connections, 20 keepalive)
- HTTP/2 support enabled
- Automatic redirect following
- Custom User-Agent header with bot version
- Timeout settings (10s connect, 30s read, 10s write, 5s pool)

Thread Safety
-------------
The client uses an asyncio.Lock for thread-safe lazy initialization.
Multiple coroutines can safely call methods concurrently.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from tux.shared.version import get_version

__all__ = ["HTTPClient", "http_client"]


class HTTPClient:
    """Centralized HTTP client service with connection pooling and proper configuration.

    This class manages a shared httpx.AsyncClient instance with lazy initialization,
    ensuring efficient connection reuse across all bot HTTP operations.

    Attributes
    ----------
    _client : httpx.AsyncClient | None
        The underlying HTTP client instance (None until first use)
    _lock : asyncio.Lock
        Thread-safe initialization lock

    Notes
    -----
    Use the module-level `http_client` singleton instead of creating instances directly.
    """

    def __init__(self) -> None:
        """Initialize the HTTP client service.

        The actual httpx.AsyncClient is not created until first use,
        following lazy initialization pattern for efficiency.
        """
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client instance.

        Uses double-checked locking pattern for thread-safe lazy initialization.
        The client is created once on first call and reused for all subsequent requests.

        Returns
        -------
        httpx.AsyncClient
            The configured HTTP client instance with connection pooling.

        Notes
        -----
        This method is automatically called by all request methods (get, post, etc.).
        You typically don't need to call this directly.
        """
        if self._client is None:
            async with self._lock:
                # Double-check after acquiring lock
                if self._client is None:
                    self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.AsyncClient:
        """Create a new HTTP client with optimal configuration.

        Configuration includes:
        - Connection pooling (100 max connections, 20 keepalive)
        - HTTP/2 support for performance
        - Automatic redirect following
        - Custom User-Agent with bot version
        - Comprehensive timeout settings

        Returns
        -------
        httpx.AsyncClient
            Configured HTTP client instance ready for use.
        """
        timeout = httpx.Timeout(
            connect=10.0,  # Time to establish connection
            read=30.0,  # Time to read response
            write=10.0,  # Time to send request
            pool=5.0,  # Time to acquire connection from pool
        )

        limits = httpx.Limits(
            max_keepalive_connections=20,  # Persistent connections
            max_connections=100,  # Total connection limit
            keepalive_expiry=30.0,  # Keep connections alive for 30s
        )

        headers = {
            "User-Agent": f"Tux-Bot/{get_version()} (https://github.com/allthingslinux/tux)",
        }

        client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            headers=headers,
            http2=True,  # Enable HTTP/2 for better performance
            follow_redirects=True,  # Auto-follow redirects
        )

        logger.debug("HTTP client created with connection pooling enabled")
        return client

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources.

        This method should be called during bot shutdown to properly close
        all connections and release resources.

        Notes
        -----
        Called automatically by the bot's shutdown process in `bot._close_connections()`.
        After calling close(), the client will be recreated on next use (lazy init).
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP client closed")

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request.

        Parameters
        ----------
        url : str
            The URL to request.
        **kwargs : Any
            Additional arguments passed to httpx.AsyncClient.get()
            (e.g., params, headers, timeout, etc.)

        Returns
        -------
        httpx.Response
            The HTTP response.

        Examples
        --------
        >>> response = await http_client.get(
        ...     "https://api.github.com/repos/allthingslinux/tux"
        ... )
        >>> data = response.json()
        """
        client = await self.get_client()
        response = await client.get(url, **kwargs)
        response.raise_for_status()
        return response

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request.

        Parameters
        ----------
        url : str
            The URL to request.
        **kwargs : Any
            Additional arguments passed to httpx.AsyncClient.post()
            (e.g., json, data, headers, timeout, etc.)

        Returns
        -------
        httpx.Response
            The HTTP response.

        Examples
        --------
        >>> response = await http_client.post(
        ...     "https://api.example.com/submit", json={"message": "hello"}
        ... )
        """
        client = await self.get_client()
        response = await client.post(url, **kwargs)
        response.raise_for_status()
        return response

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a PUT request.

        Parameters
        ----------
        url : str
            The URL to request.
        **kwargs : Any
            Additional arguments passed to httpx.AsyncClient.put()

        Returns
        -------
        httpx.Response
            The HTTP response.
        """
        client = await self.get_client()
        response = await client.put(url, **kwargs)
        response.raise_for_status()
        return response

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a DELETE request.

        Parameters
        ----------
        url : str
            The URL to request.
        **kwargs : Any
            Additional arguments passed to httpx.AsyncClient.delete()

        Returns
        -------
        httpx.Response
            The HTTP response.
        """
        client = await self.get_client()
        response = await client.delete(url, **kwargs)
        response.raise_for_status()
        return response

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Make a request with the specified HTTP method.

        Parameters
        ----------
        method : str
            The HTTP method to use (GET, POST, PUT, DELETE, PATCH, etc.).
        url : str
            The URL to request.
        **kwargs : Any
            Additional arguments passed to httpx.AsyncClient.request()

        Returns
        -------
        httpx.Response
            The HTTP response.

        Examples
        --------
        >>> response = await http_client.request(
        ...     "PATCH", "https://api.example.com/update"
        ... )
        """
        client = await self.get_client()
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response


# Global HTTP client singleton
#
# This singleton is used throughout the bot for all HTTP requests.
#
# Lifecycle:
# ----------
# 1. Created on module import (but AsyncClient not yet initialized)
# 2. AsyncClient created lazily on first HTTP request
# 3. Reused for all subsequent requests (connection pooling)
# 4. Closed during bot shutdown via bot._close_connections()
#
# Usage:
# ------
# from tux.services.http_client import http_client
# response = await http_client.get("https://api.example.com")
#
# Benefits:
# ---------
# - Connection pooling across all bot HTTP operations
# - Consistent timeout and retry configuration
# - Proper User-Agent headers
# - HTTP/2 support for better performance
# - Centralized resource cleanup
http_client = HTTPClient()
