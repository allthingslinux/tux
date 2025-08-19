from __future__ import annotations

import discord
from discord.ext import commands
from loguru import logger

from tux.core.interfaces import IDatabaseService
from tux.core.types import Tux
from tux.database.controllers import DatabaseController


def _resolve_bot(source: commands.Context[Tux] | discord.Interaction | Tux) -> Tux | None:
    """Resolve the bot instance from various source types.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction | Tux
        The source object to resolve the bot from.

    Returns
    -------
    Tux | None
        The resolved bot instance, or None if resolution fails.
    """
    if isinstance(source, commands.Context):
        return source.bot
    return source.client if isinstance(source, discord.Interaction) else source


def get_db_service_from(source: commands.Context[Tux] | discord.Interaction | Tux) -> IDatabaseService | None:
    """Get the database service from various source types.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction | Tux
        The source object to get the database service from.

    Returns
    -------
    IDatabaseService | None
        The database service instance, or None if not available.
    """
    bot = _resolve_bot(source)
    if bot is None:
        return None
    container = getattr(bot, "container", None)
    if container is None:
        return None
    try:
        return container.get_optional(IDatabaseService)
    except Exception as e:
        logger.debug(f"Failed to resolve IDatabaseService from container: {e}")
        return None


def get_db_controller_from(
    source: commands.Context[Tux] | discord.Interaction | Tux,
    *,
    fallback_to_direct: bool = True,
) -> DatabaseController | None:
    """Get the database controller from various source types.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction | Tux
        The source object to get the database controller from.
    fallback_to_direct : bool, optional
        Whether to fallback to creating a direct DatabaseController instance
        if the service-based approach fails, by default True.

    Returns
    -------
    DatabaseController | None
        The database controller instance, or None if not available and
        fallback_to_direct is False.
    """
    db_service = get_db_service_from(source)
    if db_service is not None:
        try:
            return db_service.get_controller()
        except Exception as e:
            logger.debug(f"Failed to get controller from IDatabaseService: {e}")
    return DatabaseController() if fallback_to_direct else None
