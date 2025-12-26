"""Cog setup service for bot initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands
from loguru import logger

from tux.core.cog_loader import CogLoader
from tux.core.setup.base import BotSetupService

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = ["CogSetupService"]


class CogSetupService(BotSetupService):
    """Handles cog loading and plugin setup during bot initialization."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the cog setup service.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance to load cogs for.
        """
        super().__init__(bot, "cogs")

    async def setup(self) -> None:
        """Load all cogs and plugins."""
        await self._load_jishaku()
        await self._load_cogs()
        await self._load_hot_reload()

    async def _load_jishaku(self) -> None:
        """Load Jishaku development plugin."""
        try:
            await self.bot.load_extension("jishaku")
            logger.success("Jishaku plugin loaded")
        except commands.ExtensionError as e:
            logger.warning(f"Jishaku plugin not loaded: {e}")

    async def _load_cogs(self) -> None:
        """Load all bot cogs using CogLoader."""
        logger.info("Loading cogs...")
        await CogLoader.setup(self.bot)
        logger.success("All cogs loaded")

    async def _load_hot_reload(self) -> None:
        """Load hot reload system."""
        if "tux.services.hot_reload" not in self.bot.extensions:
            try:
                await self.bot.load_extension("tux.services.hot_reload")
                logger.success("Hot reload system initialized")
            except Exception as e:
                logger.warning(f"Hot reload failed to load: {e}")
