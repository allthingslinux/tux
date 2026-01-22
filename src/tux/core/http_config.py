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


def _try_set_connector_attr(
    connector: aiohttp.TCPConnector,
    name: str,
    value: int | float,
    *,
    seconds_suffix: bool = False,
    configured: dict[str, str | int | float] | None = None,
    failed: list[str] | None = None,
) -> None:
    """Try to set a connector attribute, recording success or failure.

    Parameters
    ----------
    connector : aiohttp.TCPConnector
        The connector to configure.
    name : str
        The attribute name to set.
    value : int | float
        The value to set.
    seconds_suffix : bool, optional
        Whether to append "s" suffix when logging the value, by default False.
    configured : dict[str, str | int | float] | None, optional
        Dictionary to record successfully configured attributes, by default None.
    failed : list[str] | None, optional
        List to record failed attribute names, by default None.
    """
    if not hasattr(connector, name):
        if failed is not None:
            failed.append(name)
        return

    try:
        setattr(connector, name, value)
    except (AttributeError, TypeError):
        # Expected for read-only / ctor-only attributes
        if failed is not None:
            failed.append(name)
    else:
        if configured is not None:
            configured[name] = f"{value}s" if seconds_suffix else value


def configure_discord_http_client(bot: Tux) -> None:
    """Configure discord.py's HTTP client for high-latency environments.

    Optimizes connection pooling and DNS caching for better performance
    under network jitter (e.g., Hetzner Ashburn -> Discord).

    This function accesses discord.py's internal aiohttp ClientSession
    and configures its TCPConnector with optimized settings. Configuration
    applies to both HTTP REST API calls and WebSocket connections.

    Parameters
    ----------
    bot : Tux
        The bot instance whose HTTP client should be configured.

    Notes
    -----
    This function must be called after the bot is created but before
    connecting to Discord (e.g., in setup_hook() or __init__()).

    Most TCPConnector parameters are constructor-only and cannot be changed
    after creation. This function attempts to set them but expects failures
    for read-only properties (logged at debug level).
    """
    try:
        http_client = bot.http

        session: aiohttp.ClientSession | None = None
        if hasattr(http_client, "_HTTPClient__session"):
            session = getattr(http_client, "_HTTPClient__session", None)
        elif hasattr(http_client, "_session"):
            session = getattr(http_client, "_session", None)

        if session is None:
            logger.warning(
                "Could not find aiohttp session in HTTPClient; HTTP client "
                "configuration skipped (setup_hook() may be running before login() "
                "or discord.py internals changed).",
            )
            return

        connector = session.connector
        if connector is None or not isinstance(connector, aiohttp.TCPConnector):
            logger.warning(
                "HTTPClient session has no TCPConnector; HTTP client configuration skipped.",
            )
            return

    except AttributeError as e:
        logger.error(
            f"Failed to access HTTP client internals: {e}. "
            "HTTP client will use default settings.",
        )
        return
    except Exception:
        logger.error("Unexpected error accessing HTTP client internals", exc_info=True)
        return

    configured: dict[str, str | int | float] = {}
    failed: list[str] = []

    # Attempt to configure connector attributes
    # Most are constructor-only and will fail (expected behavior)
    _try_set_connector_attr(
        connector,
        "limit",
        100,
        configured=configured,
        failed=failed,
    )
    _try_set_connector_attr(
        connector,
        "limit_per_host",
        30,
        configured=configured,
        failed=failed,
    )
    _try_set_connector_attr(
        connector,
        "ttl_dns_cache",
        300,
        seconds_suffix=True,
        configured=configured,
        failed=failed,
    )
    _try_set_connector_attr(
        connector,
        "keepalive_timeout",
        30.0,
        seconds_suffix=True,
        configured=configured,
        failed=failed,
    )

    if configured:
        settings_str = ", ".join(f"{k}={v}" for k, v in configured.items())
        logger.info(f"Discord HTTP client configured: {settings_str}")

    if failed:
        logger.debug(
            "Could not configure HTTP client settings (expected for read-only / "
            f"ctor-only attributes): {', '.join(failed)}",
        )
