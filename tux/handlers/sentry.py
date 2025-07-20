from __future__ import annotations

from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils.sentry_manager import SentryManager

# Type alias using PEP695 syntax
type CommandObject = (
    commands.Command[Any, ..., Any] | discord.app_commands.Command[Any, ..., Any] | discord.app_commands.ContextMenu
)


class SentryHandler(commands.Cog):
    """
    Handles Sentry transaction status for completed commands.

    This cog listens for command completion events to set the Sentry
    transaction status to 'ok', complementing the error handler which
    sets failure statuses.
    """

    def __init__(self, sentry_manager: SentryManager) -> None:
        """
        Initialize the Sentry handler cog.

        Parameters
        ----------
        sentry_manager : SentryManager
            The Sentry manager instance.
        """
        self.sentry_manager = sentry_manager
        logger.info("Sentry handler initialized")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context[Tux]) -> None:
        """
        Sets the Sentry transaction status to 'ok' for a completed prefix command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        """
        if span := self.sentry_manager.get_current_span():
            span.set_status(self.sentry_manager.STATUS["OK"])
            logger.trace(f"Set Sentry span status to 'ok' for command: {ctx.command}")

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: CommandObject) -> None:
        """
        Sets the Sentry transaction status to 'ok' for a completed application command.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object
        command : CommandObject
            The command that was completed
        """
        if span := self.sentry_manager.get_current_span():
            span.set_status(self.sentry_manager.STATUS["OK"])
            logger.trace(f"Set Sentry span status to 'ok' for app command: {command.name}")


async def setup(bot: Tux) -> None:
    """Add the SentryHandler cog to the bot."""
    await bot.add_cog(SentryHandler(bot.sentry_manager))
