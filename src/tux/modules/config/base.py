"""
Base manager class for config modules.

Provides common patterns and utilities for all configuration managers
to reduce duplication and ensure consistency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tux.ui.embeds import EmbedCreator, EmbedType
from tux.ui.views.config import ConfigDashboard

if TYPE_CHECKING:
    from tux.core.bot import Tux


class BaseConfigManager:
    """Base class for configuration managers with common patterns."""

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the manager with a bot instance.

        Parameters
        ----------
        bot : Tux
            The bot instance to use for database operations.
        """
        self.bot = bot

    async def configure_dashboard(
        self,
        ctx: commands.Context[Tux],
        mode: str,
        description: str | None = None,
    ) -> None:
        """
        Open the unified config dashboard in a specific mode.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        mode : str
            The dashboard mode to open (e.g., "ranks", "roles", "commands", "logs").
        description : str | None, optional
            Optional description for the dashboard mode.
        """
        assert ctx.guild

        dashboard = ConfigDashboard(self.bot, ctx.guild, ctx.author, mode=mode)
        await dashboard.build_layout()
        await ctx.send(view=dashboard)

    def create_error_embed(self, title: str, description: str) -> discord.Embed:
        """
        Create a standardized error embed.

        Parameters
        ----------
        title : str
            Error title.
        description : str
            Error description.

        Returns
        -------
        discord.Embed
            Formatted error embed.
        """
        return EmbedCreator.create_embed(
            title=title,
            description=description,
            embed_type=EmbedType.ERROR,
            custom_color=discord.Color.red(),
        )

    def create_success_embed(self, title: str, description: str) -> discord.Embed:
        """
        Create a standardized success embed.

        Parameters
        ----------
        title : str
            Success title.
        description : str
            Success description.

        Returns
        -------
        discord.Embed
            Formatted success embed.
        """
        return EmbedCreator.create_embed(
            title=title,
            description=description,
            embed_type=EmbedType.SUCCESS,
        )

    def create_warning_embed(self, title: str, description: str) -> discord.Embed:
        """
        Create a standardized warning embed.

        Parameters
        ----------
        title : str
            Warning title.
        description : str
            Warning description.

        Returns
        -------
        discord.Embed
            Formatted warning embed.
        """
        return EmbedCreator.create_embed(
            title=title,
            description=description,
            embed_type=EmbedType.WARNING,
        )

    def create_info_embed(self, title: str, description: str) -> discord.Embed:
        """
        Create a standardized info embed.

        Parameters
        ----------
        title : str
            Info title.
        description : str
            Info description.

        Returns
        -------
        discord.Embed
            Formatted info embed.
        """
        return EmbedCreator.create_embed(
            title=title,
            description=description,
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
        )

    async def handle_error(
        self,
        ctx: commands.Context[Tux],
        error: Exception,
        operation: str,
    ) -> None:
        """
        Handle errors consistently across managers.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        error : Exception
            The error that occurred.
        operation : str
            Description of the operation that failed.
        """
        embed = self.create_error_embed(
            title=f"❌ Failed to {operation}",
            description=f"An error occurred: {error}",
        )
        await ctx.send(embed=embed)
