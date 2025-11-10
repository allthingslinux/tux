"""Configuration overview commands using unified dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from .base import BaseConfigManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class ConfigOverview(BaseConfigManager):
    """Overview and status commands for config system using unified dashboard."""

    async def overview_command(self, ctx: commands.Context[Tux]) -> None:
        """Launch the unified configuration dashboard."""
        await self.configure_dashboard(ctx, "overview")
