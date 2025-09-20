"""
Simplified help command using refactored components.

This replaces the massive 1,328-line help.py with a clean, focused implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import discord
from discord.ext import commands

from .data import HelpData
from .navigation import HelpNavigation
from .renderer import HelpRenderer


class TuxHelp(commands.HelpCommand):
    """Simplified help command using separated components."""

    def __init__(self) -> None:
        super().__init__(
            command_attrs={
                "help": "Lists all commands and sub-commands.",
                "aliases": ["h", "commands"],
                "usage": "$help <command> or <sub-command>",
            },
        )

    async def _setup_components(self) -> tuple[HelpData, HelpRenderer, HelpNavigation]:
        """Initialize help components and return them."""
        data = HelpData(self.context.bot)
        prefix = await data.get_prefix(self.context)
        renderer = HelpRenderer(prefix)
        navigation = HelpNavigation(self.context, data, renderer)
        return data, renderer, navigation

    async def send_bot_help(self, mapping: Mapping[commands.Cog | None, list[commands.Command[Any, ..., Any]]]) -> None:
        """Send the main help menu."""
        data, renderer, navigation = await self._setup_components()

        categories = await data.get_command_categories()
        embed = await renderer.create_main_embed(categories)
        view = await navigation.create_main_view()

        await self.context.send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Send help for a specific cog."""
        _, renderer, navigation = await self._setup_components()

        categories = await navigation.data.get_command_categories()
        cog_name = cog.qualified_name

        if cog_name in categories:
            commands_dict = categories[cog_name]
            embed = await renderer.create_category_embed(cog_name, commands_dict)
            view = await navigation.create_category_view(cog_name)
            await self.context.send(embed=embed, view=view)
        else:
            await self.send_error_message(f"No help available for {cog_name}")

    async def send_command_help(self, command: commands.Command[Any, Any, Any]) -> None:
        """Send help for a specific command."""
        _, renderer, navigation = await self._setup_components()

        embed = await renderer.create_command_embed(command)
        # Use simple view for direct command help
        view = await navigation.create_command_view()

        await self.context.send(embed=embed, view=view)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """Send help for a command group."""
        _, renderer, navigation = await self._setup_components()

        navigation.current_command_obj = group
        embed = await renderer.create_command_embed(group)
        view = await navigation.create_command_view()

        await self.context.send(embed=embed, view=view)

    async def send_error_message(self, error: str) -> None:
        """Send an error message."""
        embed = discord.Embed(
            title="❌ Help Error",
            description=error,
            color=discord.Color.red(),
        )
        await self.context.send(embed=embed, ephemeral=True)
