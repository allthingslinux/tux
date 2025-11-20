"""Command permission management for the config system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from .base import BaseConfigManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class CommandManager(BaseConfigManager):
    """Management commands for command permissions."""

    async def configure_commands(self, ctx: commands.Context[Tux]) -> None:
        """
        Configure command permissions using the unified config dashboard.

        This command launches the unified configuration dashboard in commands mode
        to allow administrators to assign permission ranks to moderation commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        """
        await self.configure_dashboard(ctx, "commands")
