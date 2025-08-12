"""Database utility helpers for resolving services/controllers via DI.

These helpers centralize the common pattern of retrieving the database service
and controller from the bot's dependency injection container. They accept
various sources (Context, Interaction, or Bot) and provide safe fallbacks.
"""

from __future__ import annotations

import discord
from discord.ext import commands
from loguru import logger

from tux.core.interfaces import IDatabaseService
from tux.core.types import Tux
from tux.services.database.controllers import DatabaseController


def _resolve_bot(source: commands.Context[Tux] | discord.Interaction | Tux) -> Tux | None:
    """Resolve a bot-like object from a context, interaction, or bot instance."""
    if isinstance(source, commands.Context):
        return source.bot
    return (
        source.client  # type: ignore[return-value]
        if isinstance(source, discord.Interaction)
        else source  # type: ignore[return-value]
    )


def get_db_service_from(
    source: commands.Context[Tux] | discord.Interaction | Tux,
) -> IDatabaseService | None:
    """Get `IDatabaseService` from the DI container if available.

    Returns None if the container or service isn't present.
    """
    bot = _resolve_bot(source)
    if bot is None:
        return None

    container = getattr(bot, "container", None)
    if container is None:
        return None

    try:
        return container.get_optional(IDatabaseService)  # type: ignore[attr-defined]
    except Exception as e:
        logger.debug(f"Failed to resolve IDatabaseService from container: {e}")
        return None


def get_db_controller_from(
    source: commands.Context[Tux] | discord.Interaction | Tux,
    *,
    fallback_to_direct: bool = True,
) -> DatabaseController | None:
    """Get a `DatabaseController` using DI when available.

    If `fallback_to_direct` is True and DI is unavailable, returns a direct
    `DatabaseController()` instance. Otherwise returns None.
    """
    db_service = get_db_service_from(source)
    if db_service is not None:
        try:
            return db_service.get_controller()
        except Exception as e:
            logger.debug(f"Failed to get controller from IDatabaseService: {e}")

    return DatabaseController() if fallback_to_direct else None
