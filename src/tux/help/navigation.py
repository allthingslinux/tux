"""Help system navigation and UI management."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

import discord
from discord.ext import commands

from .components import (
    BackButton,
    CategorySelectMenu,
    CloseButton,
    CommandSelectMenu,
    HelpView,
    NextButton,
    PrevButton,
    SubcommandSelectMenu,
)
from .data import HelpData
from .renderer import HelpRenderer


class HelpState(Enum):
    """Navigation states for the help command."""

    MAIN = auto()
    CATEGORY = auto()
    COMMAND = auto()
    SUBCOMMAND = auto()


class HelpNavigation:
    """Manages help system navigation and UI interactions."""

    def __init__(self, ctx: commands.Context[Any], data: HelpData, renderer: HelpRenderer) -> None:
        self.ctx = ctx
        self.data = data
        self.renderer = renderer

        # Navigation state
        self.current_state = HelpState.MAIN
        self.current_category: str | None = None
        self.current_command: str | None = None
        self.current_subcommand_page = 0
        self.subcommand_pages: list[list[commands.Command[Any, Any, Any]]] = []
        self.current_command_obj: commands.Command[Any, Any, Any] | None = None

    # Protocol implementation for UI components
    @property
    def context(self) -> commands.Context[Any]:
        """Context property required by HelpCommandProtocol."""
        return self.ctx

    async def on_category_select(self, interaction: discord.Interaction, category: str) -> None:
        """Handle category selection - protocol method."""
        await self.handle_category_select(interaction, category)

    async def on_command_select(self, interaction: discord.Interaction, command_name: str) -> None:
        """Handle command selection - protocol method."""
        await self.handle_command_select(interaction, command_name)

    async def on_subcommand_select(self, interaction: discord.Interaction, subcommand_name: str) -> None:
        """Handle subcommand selection - protocol method."""
        await self.handle_subcommand_select(interaction, subcommand_name)

    async def on_back_button(self, interaction: discord.Interaction) -> None:
        """Handle back button - protocol method."""
        await self.handle_back_button(interaction)

    async def on_next_button(self, interaction: discord.Interaction) -> None:
        """Handle next button - protocol method."""
        await self.handle_next_button(interaction)

    async def on_prev_button(self, interaction: discord.Interaction) -> None:
        """Handle prev button - protocol method."""
        await self.handle_prev_button(interaction)

    async def create_main_view(self) -> HelpView:
        """Create main help view."""
        categories = await self.data.get_command_categories()
        options = self.renderer.create_category_options(categories)

        view = HelpView(self)
        view.add_item(CategorySelectMenu(self, options, "Select a category"))
        view.add_item(CloseButton())
        return view

    async def create_category_view(self, category: str) -> HelpView:
        """Create category view."""
        categories = await self.data.get_command_categories()
        commands_dict = categories.get(category, {})
        options = self.renderer.create_command_options(commands_dict)

        view = HelpView(self)
        view.add_item(CommandSelectMenu(self, options, f"Select a command from {category}"))
        view.add_item(BackButton(self))
        view.add_item(CloseButton())
        return view

    async def create_command_view(self) -> HelpView:
        """Create command view."""
        view = HelpView(self)

        if self.current_command_obj and isinstance(self.current_command_obj, commands.Group):
            subcommands = list(self.current_command_obj.commands)
            if subcommands:
                options = self.renderer.create_subcommand_options(subcommands)
                view.add_item(SubcommandSelectMenu(self, options, "Select a subcommand"))

        view.add_item(BackButton(self))
        view.add_item(CloseButton())
        return view

    async def create_subcommand_view(self) -> HelpView:
        """Create subcommand view."""
        view = HelpView(self)

        if len(self.subcommand_pages) > 1:
            if self.current_subcommand_page > 0:
                view.add_item(PrevButton(self))
            if self.current_subcommand_page < len(self.subcommand_pages) - 1:
                view.add_item(NextButton(self))

        view.add_item(BackButton(self))
        view.add_item(CloseButton())
        return view

    async def handle_category_select(self, interaction: discord.Interaction, category: str) -> None:
        """Handle category selection."""
        self.current_state = HelpState.CATEGORY
        self.current_category = category

        categories = await self.data.get_command_categories()
        commands_dict = categories.get(category, {})

        embed = await self.renderer.create_category_embed(category, commands_dict)
        view = await self.create_category_view(category)

        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_command_select(self, interaction: discord.Interaction, command_name: str) -> None:
        """Handle command selection."""
        command = self.data.find_command(command_name)
        if not command:
            await interaction.response.send_message("Command not found.", ephemeral=True)
            return

        self.current_state = HelpState.COMMAND
        self.current_command = command_name
        self.current_command_obj = command

        embed = await self.renderer.create_command_embed(command)
        view = await self.create_command_view()

        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_subcommand_select(self, interaction: discord.Interaction, subcommand_name: str) -> None:
        """Handle subcommand selection."""
        if not self.current_command_obj:
            return

        result = self.data.find_parent_command(subcommand_name)
        if not result:
            await interaction.response.send_message("Subcommand not found.", ephemeral=True)
            return

        parent_name, subcommand = result
        self.current_state = HelpState.SUBCOMMAND

        embed = await self.renderer.create_subcommand_embed(parent_name, subcommand)
        view = await self.create_subcommand_view()

        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_back_button(self, interaction: discord.Interaction) -> None:
        """Handle back button navigation."""
        if self.current_state == HelpState.CATEGORY:
            self.current_state = HelpState.MAIN
            categories = await self.data.get_command_categories()
            embed = await self.renderer.create_main_embed(categories)
            view = await self.create_main_view()
        elif self.current_state == HelpState.COMMAND:
            self.current_state = HelpState.CATEGORY
            if self.current_category:
                categories = await self.data.get_command_categories()
                commands_dict = categories.get(self.current_category, {})
                embed = await self.renderer.create_category_embed(self.current_category, commands_dict)
                view = await self.create_category_view(self.current_category)
            else:
                return
        elif self.current_state == HelpState.SUBCOMMAND:
            self.current_state = HelpState.COMMAND
            if self.current_command_obj:
                embed = await self.renderer.create_command_embed(self.current_command_obj)
                view = await self.create_command_view()
            else:
                return
        else:
            return

        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_next_button(self, interaction: discord.Interaction) -> None:
        """Handle next page navigation."""
        if self.current_subcommand_page < len(self.subcommand_pages) - 1:
            self.current_subcommand_page += 1
            view = await self.create_subcommand_view()
            await interaction.response.edit_message(view=view)

    async def handle_prev_button(self, interaction: discord.Interaction) -> None:
        """Handle previous page navigation."""
        if self.current_subcommand_page > 0:
            self.current_subcommand_page -= 1
            view = await self.create_subcommand_view()
            await interaction.response.edit_message(view=view)
