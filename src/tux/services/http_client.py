"""Centralized HTTP client service for Tux bot.

Provides a shared httpx.AsyncClient instance with connection pooling,
proper timeout configuration, and error handling for all HTTP requests.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from tux.shared.config import CONFIG


class HTTPClient:
    """Centralized HTTP client service with connection pooling and proper configuration."""

    def __init__(self) -> None:
        """Initialize the HTTP client service."""
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client instance.

        Returns
        -------
        httpx.AsyncClient
            The configured HTTP client instance.
        """
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.AsyncClient:
        """Create a new HTTP client with optimal configuration.

        Returns
        -------
        httpx.AsyncClient
            Configured HTTP client instance.
        """
        timeout = httpx.Timeout(
            connect=10.0,  # Connection timeout
            read=30.0,  # Read timeout
            write=10.0,  # Write timeout
            pool=5.0,  # Pool timeout
        )

        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )

        headers = {
            "User-Agent": f"Tux-Bot/{CONFIG.BOT_INFO.BOT_VERSION} (https://github.com/allthingslinux/tux)",
        }

        client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            headers=headers,
            http2=True,
            follow_redirects=True,
        )

        logger.debug("HTTP client created with connection pooling enabled")
        return client

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
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
            Additional arguments to pass to the request.

        Returns
        -------
        httpx.Response
            The HTTP response.
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
            Additional arguments to pass to the request.

        Returns
        -------
        httpx.Response
            The HTTP response.
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
            Additional arguments to pass to the request.

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
            Additional arguments to pass to the request.

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
        """Make a request with the specified method.

        Parameters
        ----------
        method : str
            The HTTP method to use.
        url : str
            The URL to request.
        **kwargs : Any
            Additional arguments to pass to the request.

        Returns
        -------
        httpx.Response
            The HTTP response.
        """
        client = await self.get_client()
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response


# Global HTTP client instance
http_client = HTTPClient()
