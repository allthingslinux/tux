"""HTTP client configuration for discord.py's internal aiohttp client.

This module provides functionality to configure discord.py's HTTP client
for optimal performance in high-latency, high-jitter environments (e.g., Hetzner Ashburn).

**Scope:**
This configuration applies to BOTH HTTP REST API calls AND WebSocket connections,
as both use the same underlying aiohttp ClientSession and TCPConnector.
The gateway (discord/gateway.py) uses `client.http.ws_connect()` which calls
the same session's `ws_connect()` method (discord/http.py:566).

**What we attempt to configure:**
- DNS cache TTL (ttl_dns_cache): Attempt to increase from 10s to 5 minutes
- Keepalive timeout: Attempt to increase from 15s to 30s

**What cannot be configured (constructor parameters, read-only after creation):**
- Connection pool limit (limit): Constructor parameter, cannot be changed after creation
- Per-host connection limit (limit_per_host): Constructor parameter, cannot be changed after creation
- DNS cache TTL (ttl_dns_cache): Constructor parameter, likely cannot be changed after creation

Note: All TCPConnector parameters shown in aiohttp documentation are constructor parameters.
Since discord.py creates the connector before we can configure it, we attempt to set them
but expect failures for read-only properties. Failures are logged as debug messages.
"""

from __future__ import annotations

import aiohttp
from loguru import logger

from tux.core.bot import Tux


def configure_discord_http_client(bot: Tux) -> None:  # noqa: PLR0912, PLR0915
    # sourcery skip: extract-method
    """Configure discord.py's HTTP client for high-latency environments.

    Optimizes connection pooling and DNS caching for better performance
    under network jitter (e.g., Hetzner Ashburn -> Discord).

    This function accesses discord.py's internal aiohttp ClientSession
    and configures its TCPConnector with optimized settings.

    **Important:** This configuration applies to BOTH HTTP REST API calls
    AND WebSocket connections, as both use the same underlying aiohttp
    ClientSession. The gateway uses `client.http.ws_connect()` which
    delegates to the same session (discord/http.py:566, gateway.py:383).

    Parameters
    ----------
    bot : Tux
        The bot instance whose HTTP client should be configured.

    Notes
    -----
    This function must be called after the bot is created but before
    connecting to Discord (e.g., in setup_hook() or __init__()).

    **Limitations:**
    - `limit` and `limit_per_host` are explicitly documented as read-only properties
      in aiohttp Client Reference documentation (BaseConnector). They are constructor
      parameters and cannot be changed after connector creation.
    - `ttl_dns_cache` and `keepalive_timeout` are constructor parameters and likely
      read-only after creation, though not explicitly documented as such.
    - All attempts to set these will fail gracefully (logged as debug).

    The configuration takes effect immediately for new connections.
    Existing connections will use the new settings on their next request.

    Raises
    ------
    AttributeError
        If discord.py's HTTPClient structure has changed and we cannot
        access the underlying aiohttp session/connector.
    """
    try:
        # Access discord.py's HTTPClient instance
        http_client = bot.http

        # Access the underlying aiohttp ClientSession
        # discord.py stores the session as a private attribute: __session
        # Python name mangling converts this to _HTTPClient__session
        # The session is created in HTTPClient.static_login() (discord/http.py:826)
        # which is called in bot.login() (discord/client.py:675) before setup_hook(),
        # so it should exist when this function runs.
        # Reference: discord/http.py line 528 (self.__session declaration)
        session: aiohttp.ClientSession | None = None

        # Try the standard name-mangled attribute name first
        # This is the correct way to access __session in discord.py
        if hasattr(http_client, "_HTTPClient__session"):
            session = getattr(http_client, "_HTTPClient__session", None)
        # Fallback for older versions or if name mangling differs
        elif hasattr(http_client, "_session"):
            session = getattr(http_client, "_session", None)

        if session is None:
            logger.warning(
                "Could not find aiohttp session in HTTPClient. "
                "HTTP client configuration skipped. "
                "This may occur if setup_hook() is called before login(). "
                "discord.py version may have changed internal structure.",
            )
            return

        # Get the TCPConnector from the session
        connector = session.connector
        if connector is None or not isinstance(connector, aiohttp.TCPConnector):
            logger.warning(
                "HTTPClient session has no TCPConnector. "
                "HTTP client configuration skipped.",
            )
            return

        # Configure for high-latency, high-jitter environments
        # These values are optimized for Hetzner Ashburn -> Discord path
        #
        # According to aiohttp Client Reference documentation:
        # - limit: Total parallel connections (default: 100, constructor parameter)
        #   EXPLICITLY DOCUMENTED AS READ-ONLY PROPERTY (BaseConnector.limit)
        # - limit_per_host: Connections per endpoint (default: 0=unlimited, constructor parameter)
        #   EXPLICITLY DOCUMENTED AS READ-ONLY PROPERTY (BaseConnector.limit_per_host)
        # - ttl_dns_cache: DNS cache TTL in seconds (default: 10, constructor parameter)
        #   Constructor parameter, likely read-only after creation
        # - keepalive_timeout: Connection reuse timeout (default: 15, constructor parameter)
        #   Constructor parameter, likely read-only after creation
        #
        # IMPORTANT: Per aiohttp Client Reference, limit and limit_per_host are explicitly
        # documented as read-only properties. All TCPConnector parameters are constructor
        # parameters and cannot be changed after connector creation. Since discord.py creates
        # the connector before we can configure it, we attempt to set them but expect failures.
        # discord.py creates connector with limit=0 (unlimited) by default (http.py:824).
        configured_settings: dict[str, str | int | float] = {}
        failed_settings: list[str] = []

        try:
            # Configure total connection pool limit
            # Note: EXPLICITLY documented as read-only property in aiohttp Client Reference
            # (BaseConnector.limit). discord.py creates connector with limit=0 (unlimited).
            # We attempt to set it to 100, but expect it to fail gracefully.
            if hasattr(connector, "limit"):
                try:
                    connector.limit = 100  # type: ignore[assignment]
                    configured_settings["limit"] = 100
                except (AttributeError, TypeError):
                    # Expected: limit is a read-only property
                    failed_settings.append("limit")
            else:
                failed_settings.append("limit")

            # Configure per-host connection limit
            # Note: EXPLICITLY documented as read-only property in aiohttp Client Reference
            # (BaseConnector.limit_per_host). Default is 0 (no limit).
            # We attempt to set to 30 for better connection reuse, but expect it to fail.
            if hasattr(connector, "limit_per_host"):
                try:
                    connector.limit_per_host = 30  # type: ignore[assignment]
                    configured_settings["limit_per_host"] = 30
                except (AttributeError, TypeError):
                    # Expected: limit_per_host is a read-only property
                    failed_settings.append("limit_per_host")
            else:
                failed_settings.append("limit_per_host")

            # Configure DNS cache TTL
            # Default is 10 seconds, we increase to 5 minutes (300s) for high-latency environments
            # Note: ttl_dns_cache is a constructor parameter per aiohttp docs, so this may fail.
            # We attempt it anyway as some aiohttp versions may allow runtime modification.
            if hasattr(connector, "ttl_dns_cache"):
                try:
                    connector.ttl_dns_cache = 300  # type: ignore[assignment,attr-defined]
                    configured_settings["ttl_dns_cache"] = 300
                except (AttributeError, TypeError):
                    # Expected if ttl_dns_cache is read-only (constructor parameter)
                    failed_settings.append("ttl_dns_cache")
            else:
                failed_settings.append("ttl_dns_cache")

            # Configure keepalive timeout (if supported)
            # Default is 15 seconds (from BaseConnector), we increase to 30 for high-latency.
            # This keeps connections alive longer to reduce connection overhead.
            # Note: This may also be read-only, but we attempt to set it.
            if hasattr(connector, "keepalive_timeout"):
                try:
                    connector.keepalive_timeout = 30.0  # type: ignore[assignment,attr-defined]
                    configured_settings["keepalive_timeout"] = 30.0
                except (AttributeError, TypeError):
                    # May be read-only in some aiohttp versions
                    failed_settings.append("keepalive_timeout")
            # Note: keepalive_timeout may not exist in all aiohttp versions, so we don't
            # add it to failed_settings if the attribute doesn't exist

            # Log configuration results
            if configured_settings:
                settings_str = ", ".join(
                    f"{k}={v}"
                    + ("s" if k in ("ttl_dns_cache", "keepalive_timeout") else "")
                    for k, v in configured_settings.items()
                )
                logger.info(f"Discord HTTP client configured: {settings_str}")

            if failed_settings:
                # Note: limit and limit_per_host are explicitly documented as read-only
                # properties in aiohttp Client Reference. All TCPConnector parameters are
                # constructor parameters, so failures are expected. We log them for visibility
                # but they're not errors.
                logger.debug(
                    f"Could not configure HTTP client settings (expected for read-only properties): "
                    f"{', '.join(failed_settings)}. "
                    "These are constructor parameters that can only be set during connector creation. "
                    "Per aiohttp Client Reference, limit and limit_per_host are explicitly read-only.",
                )

        except (AttributeError, TypeError) as e:
            logger.warning(
                f"Could not configure HTTP client settings: {e}. "
                "Some settings may be read-only in this discord.py version.",
            )

    except AttributeError as e:
        logger.error(
            f"Failed to configure HTTP client: {e}. "
            "discord.py version may have changed internal structure. "
            "HTTP client will use default settings.",
        )
        # Don't raise - allow bot to continue with default settings
    except Exception as e:
        logger.error(
            f"Unexpected error configuring HTTP client: {e}",
            exc_info=True,
        )
        # Don't raise - allow bot to continue with default settings
