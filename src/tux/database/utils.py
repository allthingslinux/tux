from __future__ import annotations

from typing import TypeVar

import discord
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.database.controllers import DatabaseCoordinator
from tux.database.controllers.base import BaseController
from tux.database.service import DatabaseService

ModelT = TypeVar("ModelT")


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
    if isinstance(source, discord.Interaction):
        return source.client if isinstance(source.client, Tux) else None
    return source


def get_db_service_from(source: commands.Context[Tux] | discord.Interaction | Tux) -> DatabaseService | None:
    """Get the database service from various source types.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction | Tux
        The source object to get the database service from.

    Returns
    -------
    DatabaseService | None
        The database service instance, or None if not available.
    """
    bot = _resolve_bot(source)
    if bot is None:
        return None
    container = getattr(bot, "container", None)
    if container is None:
        return None
    try:
        # Try to get DatabaseService directly
        db_service = container.get_optional(DatabaseService)
        if db_service is not None:
            return db_service

    except Exception as e:
        logger.debug(f"Failed to resolve DatabaseService from container: {e}")
    return None


def get_db_controller_from(
    source: commands.Context[Tux] | discord.Interaction | Tux,
    *,
    fallback_to_direct: bool = True,
) -> DatabaseCoordinator | None:
    """Get the database coordinator from various source types.

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction | Tux
        The source object to get the database coordinator from.
    fallback_to_direct : bool, optional
        Whether to fallback to creating a direct DatabaseCoordinator instance
        if the service-based approach fails, by default True.

    Returns
    -------
    DatabaseCoordinator | None
        The database coordinator instance, or None if not available and
        fallback_to_direct is False.
    """
    db_service = get_db_service_from(source)
    if db_service is not None:
        try:
            # Create a simple coordinator wrapper
            return DatabaseCoordinator(db_service)
        except Exception as e:
            logger.debug(f"Failed to get coordinator from DatabaseService: {e}")
    return DatabaseCoordinator() if fallback_to_direct else None


def create_enhanced_controller_from[ModelT](
    source: commands.Context[Tux] | discord.Interaction | Tux,
    model: type[ModelT],
) -> BaseController[ModelT] | None:
    """Create an enhanced BaseController instance from various source types.

    This provides access to the new enhanced controller pattern with:
    - Sentry integration
    - Transaction management
    - Better error handling
    - Query performance monitoring

    Parameters
    ----------
    source : commands.Context[Tux] | discord.Interaction | Tux
        The source object to get the database service from.
    model : type[ModelT]
        The SQLModel class to create a controller for.

    Returns
    -------
    BaseController[ModelT] | None
        The enhanced controller instance, or None if not available.
    """
    db_service = get_db_service_from(source)
    if db_service is not None:
        try:
            return BaseController(model, db_service)
        except Exception as e:
            logger.debug(f"Failed to create enhanced controller: {e}")
    return None
