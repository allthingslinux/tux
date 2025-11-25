"""Sentry integration cog for command tracking and context enrichment."""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.services.sentry import (
    set_command_context,
    set_user_context,
    track_command_end,
    track_command_start,
)


class SentryHandler(commands.Cog):
    """Handles Sentry context enrichment and command performance tracking."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Sentry handler cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach the handler to.
        """
        self.bot = bot

    @commands.Cog.listener("on_command")
    async def on_command(self, ctx: commands.Context[Tux]) -> None:
        """Track command start and set context for prefix commands."""
        if ctx.command:
            # Set enhanced Sentry context
            set_command_context(ctx)
            set_user_context(ctx.author)

            # Start performance tracking
            track_command_start(ctx.command.qualified_name)

    @commands.Cog.listener("on_command_completion")
    async def on_command_completion(self, ctx: commands.Context[Tux]) -> None:
        """Track successful command completion."""
        if ctx.command:
            track_command_end(ctx.command.qualified_name, success=True)

    @commands.Cog.listener("on_app_command_completion")
    async def on_app_command_completion(self, interaction: discord.Interaction) -> None:
        """Track successful app command completion."""
        if interaction.command:
            # Set context for app commands
            set_command_context(interaction)
            set_user_context(interaction.user)

            # Track completion (command_type will be determined in track_command_end)
            track_command_end(interaction.command.qualified_name, success=True)

    async def cog_load(self) -> None:
        """Log when cog is loaded."""
        logger.debug("Sentry handler cog loaded")

    async def cog_unload(self) -> None:
        """Log when cog is unloaded."""
        logger.debug("Sentry handler cog unloaded")


async def setup(bot: Tux) -> None:
    """Cog setup for Sentry handler.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(SentryHandler(bot))
