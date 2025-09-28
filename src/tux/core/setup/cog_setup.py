"""Cog setup service for bot initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from tux.core.cog_loader import CogLoader
from tux.core.setup.base import BotSetupService

if TYPE_CHECKING:
    from tux.core.bot import Tux


class CogSetupService(BotSetupService):
    """Handles cog loading and plugin setup during bot initialization."""

    def __init__(self, bot: Tux) -> None:
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
            self._log_step("Jishaku plugin loaded", "success")
        except commands.ExtensionError as e:
            self._log_step(f"Jishaku plugin not loaded: {e}", "warning")

    async def _load_cogs(self) -> None:
        """Load all bot cogs using CogLoader."""
        self._log_step("Loading cogs...")
        await CogLoader.setup(self.bot)
        self._log_step("All cogs loaded", "success")

    async def _load_hot_reload(self) -> None:
        """Load hot reload system."""
        if "tux.services.hot_reload" not in self.bot.extensions:
            try:
                await self.bot.load_extension("tux.services.hot_reload")
                self._log_step("Hot reload system initialized", "success")
            except Exception as e:
                self._log_step(f"Hot reload failed to load: {e}", "warning")
