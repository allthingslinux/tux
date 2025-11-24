"""
Simplified help command using refactored components.

This replaces the massive 1,328-line help.py with a clean, focused implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from discord.ext import commands
from loguru import logger

from tux.ui.embeds import EmbedCreator

from .components import DirectHelpView
from .data import HelpData
from .navigation import HelpNavigation
from .renderer import HelpRenderer
from .utils import paginate_items


class TuxHelp(commands.HelpCommand):
    """Simplified help command using separated components."""

    def __init__(self) -> None:
        """Initialize the Tux help command.

        Sets up the help command with standard attributes and aliases.
        """
        super().__init__(
            command_attrs={
                "help": "Lists all commands and sub-commands.",
                "aliases": ["h", "commands"],
                "usage": "help <command> or <sub-command>",
            },
        )

    async def _setup_components(self) -> tuple[HelpData, HelpRenderer, HelpNavigation]:
        """
        Initialize help components and return them.

        Returns
        -------
        tuple[HelpData, HelpRenderer, HelpNavigation]
            Tuple of (data, renderer, navigation) components.
        """
        data = HelpData(self.context.bot, self.context)
        prefix = await data.get_prefix(self.context)
        renderer = HelpRenderer(prefix)
        navigation = HelpNavigation(self.context, data, renderer)
        return data, renderer, navigation

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, ..., Any]]],
    ) -> None:
        """Send the main help menu."""
        data, renderer, navigation = await self._setup_components()

        categories = await data.get_command_categories()
        embed = await renderer.create_main_embed(categories)
        view = await navigation.create_main_view()

        await self.context.send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Send help for a specific cog."""
        data, renderer, navigation = await self._setup_components()

        categories = await data.get_command_categories()
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
        view = await navigation.create_command_view()

        await self.context.send(embed=embed, view=view)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """Send help for a command group."""
        data, renderer, navigation = await self._setup_components()

        navigation.current_command_obj = group
        navigation.current_command = group.name

        # Filter subcommands based on permissions
        filtered_subcommands = [
            cmd for cmd in group.commands if await data.can_run_command(cmd)
        ]

        # For large command groups or JSK, use pagination
        if group.name in {"jsk", "jishaku"} or len(filtered_subcommands) > 15:
            # Paginate filtered subcommands
            subcommands = sorted(filtered_subcommands, key=lambda x: x.name)
            pages = paginate_items(subcommands, 8)

            # Create direct help view with navigation
            view = DirectHelpView(navigation, group, pages)
            embed = await view.get_embed()

        else:
            embed = await renderer.create_command_embed(group)
            view = await navigation.create_command_view()

        await self.context.send(embed=embed, view=view)

    async def send_error_message(self, error: str) -> None:
        """Send an error message."""
        embed = EmbedCreator.create_embed(
            EmbedCreator.ERROR,
            user_name=self.context.author.name,
            user_display_avatar=self.context.author.display_avatar.url,
            description=error,
        )

        await self.get_destination().send(embed=embed)

        # Only log errors that are not related to command not found
        if "no command called" not in error.lower():
            logger.warning(f"An error occurred while sending a help message: {error}")
