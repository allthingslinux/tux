"""Sentry configuration and setup."""

from __future__ import annotations

import asyncio
import logging
import signal
from types import FrameType
from typing import Any

import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration

from tux.shared.config import CONFIG
from tux.shared.version import get_version

from .handlers import before_send, before_send_transaction, traces_sampler


def setup() -> None:
    """Initialize Sentry SDK with configuration."""
    if not CONFIG.EXTERNAL_SERVICES.SENTRY_DSN:
        logger.info("Sentry DSN not provided, skipping Sentry initialization.")
        return

    logger.info("Initializing Sentry...")

    sentry_sdk.init(
        dsn=CONFIG.EXTERNAL_SERVICES.SENTRY_DSN,
        release=get_version(),
        environment="development" if CONFIG.DEBUG else "production",
        integrations=[
            AsyncioIntegration(),
            LoguruIntegration(
                level=logging.DEBUG,  # Capture all logs as breadcrumbs for context
                event_level=logging.ERROR,  # Only send ERROR+ as full Sentry events
            ),
        ],
        before_send=before_send,
        before_send_transaction=before_send_transaction,
        traces_sampler=traces_sampler,
        profiles_sample_rate=0.0,
        enable_tracing=True,
        debug=False,  # Disabled to prevent Sentry's internal debug logs from bypassing Loguru
        attach_stacktrace=True,
        send_default_pii=False,
        max_breadcrumbs=50,
        shutdown_timeout=5,
    )

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, report_signal)
    signal.signal(signal.SIGINT, report_signal)

    logger.success("Sentry initialized successfully.")


def _set_signal_scope_tags(scope: Any, signum: int) -> None:
    """Set scope tags for signal handling."""
    signal_names = {
        signal.SIGTERM.value: "SIGTERM",
        signal.SIGINT.value: "SIGINT",
    }

    scope.set_tag("signal.received", signal_names.get(signum, f"SIGNAL_{signum}"))
    scope.set_tag("shutdown.reason", "signal")
    scope.set_context(
        "signal",
        {
            "number": signum,
            "name": signal_names.get(signum, f"UNKNOWN_{signum}"),
        },
    )


def report_signal(signum: int, _frame: FrameType | None) -> None:
    """Report signal reception to Sentry."""
    if not is_initialized():
        return

    with sentry_sdk.push_scope() as scope:
        _set_signal_scope_tags(scope, signum)

        signal_name = {
            signal.SIGTERM.value: "SIGTERM",
            signal.SIGINT.value: "SIGINT",
        }.get(signum, f"SIGNAL_{signum}")

        # Add more context to the message to avoid "(No error message)" in Sentry
        message = (
            f"Received {signal_name}, initiating graceful shutdown. "
            f"This is a normal shutdown signal, not an error."
        )

        scope.set_context(
            "signal_details",
            {
                "signal_number": signum,
                "signal_name": signal_name,
                "shutdown_type": "graceful",
                "is_error": False,
            },
        )

        sentry_sdk.capture_message(message, level="info")

        logger.info(f"Signal {signal_name} reported to Sentry")


def flush() -> None:
    """Flush pending Sentry events."""
    if not is_initialized():
        return

    logger.info("Flushing Sentry events...")

    try:
        sentry_sdk.flush(timeout=10)
        logger.success("Sentry events flushed successfully.")
    except Exception as e:
        logger.error(f"Failed to flush Sentry events: {e}")


async def flush_async(flush_timeout: float = 10.0) -> None:
    """Flush pending Sentry events asynchronously."""
    if not is_initialized():
        return

    logger.info("Flushing Sentry events asynchronously...")

    try:
        # Run the blocking flush operation in a thread pool
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: sentry_sdk.flush(timeout=flush_timeout),
        )
        logger.success("Sentry events flushed successfully.")
    except TimeoutError:
        logger.warning(f"Sentry flush timed out after {flush_timeout}s")
    except Exception as e:
        logger.error(f"Failed to flush Sentry events: {e}")


def is_initialized() -> bool:
    """Check if Sentry is initialized.

    Returns
    -------
    bool
        True if Sentry is initialized, False otherwise.
    """
    return sentry_sdk.Hub.current.client is not None
