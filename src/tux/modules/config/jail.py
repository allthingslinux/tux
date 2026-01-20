"""Jail channel and role configuration using the unified dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from .base import BaseConfigManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class JailManager(BaseConfigManager):
    """Management for jail channel and jail role configuration."""

    async def configure_jail(self, ctx: commands.Context[Tux]) -> None:
        """
        Configure the jail channel and jail role using the unified config dashboard.

        This command launches the configuration dashboard in jail mode so
        administrators can set the channel where jailed members can communicate
        and the role that restricts their access to the rest of the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        """
        await self.configure_dashboard(ctx, "jail")
