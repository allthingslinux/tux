"""Help system navigation and UI management."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

import discord
from discord.ext import commands
from loguru import logger

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
from .utils import format_multiline_description, paginate_items


class HelpState(Enum):
    """Navigation states for the help command."""

    MAIN = auto()
    CATEGORY = auto()
    COMMAND = auto()
    SUBCOMMAND = auto()


class HelpNavigation:
    """Manages help system navigation and UI interactions."""

    def __init__(
        self,
        ctx: commands.Context[Any],
        data: HelpData,
        renderer: HelpRenderer,
    ) -> None:
        """Initialize the help navigation manager.

        Parameters
        ----------
        ctx : commands.Context[Any]
            The Discord context for the help command.
        data : HelpData
            The help data manager instance.
        renderer : HelpRenderer
            The help renderer instance.
        """
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

    async def on_category_select(
        self,
        interaction: discord.Interaction,
        category: str,
    ) -> None:
        """Handle category selection - protocol method."""
        await self.handle_category_select(interaction, category)

    async def on_command_select(
        self,
        interaction: discord.Interaction,
        command_name: str,
    ) -> None:
        """Handle command selection - protocol method."""
        await self.handle_command_select(interaction, command_name)

    async def on_subcommand_select(
        self,
        interaction: discord.Interaction,
        subcommand_name: str,
    ) -> None:
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

    def _paginate_subcommands(
        self,
        commands_list: list[commands.Command[Any, Any, Any]],
        preserve_page: bool = False,
    ) -> None:
        """Split subcommands into pages for pagination."""
        current_page = self.current_subcommand_page if preserve_page else 0
        self.subcommand_pages = paginate_items(commands_list, 10)

        # Restore or reset page counter
        if preserve_page:
            # Make sure the page index is valid for the new pagination
            self.current_subcommand_page = min(
                current_page,
                len(self.subcommand_pages) - 1,
            )
        else:
            # Reset to first page when paginating
            self.current_subcommand_page = 0

    async def _create_paginated_embed(self) -> discord.Embed:
        """
        Create an embed showing the current page of subcommands.

        Returns
        -------
        discord.Embed
            The embed for the current subcommand page.
        """
        if not self.current_command_obj:
            # Create a basic embed if no command object
            return self.renderer.create_base_embed(
                "Help",
                "No command information available.",
            )

        if not isinstance(self.current_command_obj, commands.Group):
            # Fallback to regular embed if not a group
            return await self.renderer.create_command_embed(self.current_command_obj)

        valid_page = self.subcommand_pages and 0 <= self.current_subcommand_page < len(
            self.subcommand_pages,
        )
        current_page_cmds = (
            self.subcommand_pages[self.current_subcommand_page] if valid_page else []
        )

        # Create embed similar to command embed but with paginated subcommands
        help_text = format_multiline_description(self.current_command_obj.help)
        embed = self.renderer.create_base_embed(
            title=f"{self.renderer.prefix}{self.current_command_obj.qualified_name}",
            description=help_text,
        )

        await self.renderer.add_command_help_fields(embed, self.current_command_obj)

        # Add flag details if present
        if flag_details := self.renderer.format_flag_details(self.current_command_obj):
            embed.add_field(
                name="Flags",
                value=f"```\n{flag_details}\n```",
                inline=False,
            )

        # Show current page subcommands
        if current_page_cmds:
            page_num = self.current_subcommand_page + 1
            total_pages = len(self.subcommand_pages)

            subcommands_list = "\n".join(
                f"• `{c.name}`{' ≡' if isinstance(c, commands.Group) and c.commands else ''} - {c.short_doc or 'No description'}"
                for c in current_page_cmds
            )
            embed.add_field(
                name=f"Subcommands (Page {page_num}/{total_pages})",
                value=f"Showing {len(current_page_cmds)} of {sum(len(page) for page in self.subcommand_pages)} subcommands:\n\n{subcommands_list}",
                inline=False,
            )

        return embed

    async def _find_parent_command(
        self,
        subcommand_name: str,
    ) -> tuple[str, commands.Command[Any, Any, Any]] | None:
        """
        Find the parent command for a given subcommand.

        Returns
        -------
        tuple[str, commands.Command[Any, Any, Any]] | None
            Tuple of (parent_name, parent_command) if found, None otherwise.
        """
        if not self.data.command_mapping:
            return None

        for category_commands in self.data.command_mapping.values():
            for parent_name, cmd in category_commands.items():
                if isinstance(cmd, commands.Group) and discord.utils.get(
                    cmd.commands,
                    name=subcommand_name,
                ):
                    return parent_name, cmd
        return None

    async def create_main_view(self) -> HelpView:
        """
        Create main help view.

        Returns
        -------
        HelpView
            The main help view with category selection.
        """
        categories = await self.data.get_command_categories()
        options = self.renderer.create_category_options(categories)

        view = HelpView(self)
        view.add_item(CategorySelectMenu(self, options, "Select a category"))
        view.add_item(CloseButton())
        return view

    async def create_category_view(self, category: str) -> HelpView:
        """
        Create category view.

        Returns
        -------
        HelpView
            The category view with command selection.
        """
        categories = await self.data.get_command_categories()
        commands_dict = categories.get(category, {})
        command_mapping = (
            self.data.command_mapping.get(category, {})
            if self.data.command_mapping
            else {}
        )
        options = self.renderer.create_command_options(commands_dict, command_mapping)

        view = HelpView(self)
        view.add_item(
            CommandSelectMenu(self, options, f"Select a command from {category}"),
        )
        view.add_item(CloseButton())
        view.add_item(BackButton(self))
        return view

    async def create_command_view(self) -> HelpView:
        """
        Create command view.

        Returns
        -------
        HelpView
            The command view with command details and navigation.
        """
        view = HelpView(self)

        # Add close button first
        view.add_item(CloseButton())

        # If this is a command group, handle navigation
        if (
            self.current_command_obj
            and isinstance(self.current_command_obj, commands.Group)
            and self.current_command_obj.commands
        ):
            # Filter subcommands based on user permissions
            filtered_cmds = [
                cmd
                for cmd in self.current_command_obj.commands
                if await self.data.can_run_command(cmd)
            ]
            sorted_cmds = sorted(filtered_cmds, key=lambda x: x.name)

            # For large command groups like JSK, use pagination buttons and add a select menu for the current page
            if (
                self.current_command_obj.name in {"jsk", "jishaku"}
                or len(sorted_cmds) > 15
            ):
                if not self.subcommand_pages:
                    self._paginate_subcommands(sorted_cmds, preserve_page=True)

                if len(self.subcommand_pages) > 1:
                    view.add_item(PrevButton(self))
                    view.add_item(NextButton(self))

                valid_page = (
                    self.subcommand_pages
                    and 0 <= self.current_subcommand_page < len(self.subcommand_pages)
                )
                current_page_cmds = (
                    self.subcommand_pages[self.current_subcommand_page]
                    if valid_page
                    else []
                )
                if not valid_page:
                    logger.warning(
                        f"Invalid page index: {self.current_subcommand_page}, pages: {len(self.subcommand_pages)}",
                    )

                if jsk_select_options := [
                    discord.SelectOption(
                        label=cmd.name,
                        value=cmd.name,
                        description=cmd.short_doc or "No description",
                    )
                    for cmd in current_page_cmds
                ]:
                    jsk_select = SubcommandSelectMenu(
                        self,
                        jsk_select_options,
                        "Select a subcommand",
                    )
                    view.add_item(jsk_select)
            else:
                logger.info(
                    f"Creating dropdown for command group: {self.current_command_obj.name} with {len(sorted_cmds)} subcommands",
                )

                if subcommand_options := self.renderer.create_subcommand_options(
                    sorted_cmds,
                ):
                    subcommand_select = SubcommandSelectMenu(
                        self,
                        subcommand_options,
                        "Select a subcommand",
                    )
                    view.add_item(subcommand_select)

        # Add back button last
        view.add_item(BackButton(self))

        return view

    async def create_subcommand_view(self) -> HelpView:
        """
        Create subcommand view.

        Returns
        -------
        HelpView
            The subcommand view with subcommand details.
        """
        view = HelpView(self)

        if len(self.subcommand_pages) > 1:
            if self.current_subcommand_page > 0:
                view.add_item(PrevButton(self))
            if self.current_subcommand_page < len(self.subcommand_pages) - 1:
                view.add_item(NextButton(self))

        view.add_item(CloseButton())
        view.add_item(BackButton(self))
        return view

    async def handle_category_select(
        self,
        interaction: discord.Interaction,
        category: str,
    ) -> None:
        """Handle category selection."""
        self.current_state = HelpState.CATEGORY
        self.current_category = category

        categories = await self.data.get_command_categories()
        commands_dict = categories.get(category, {})

        embed = await self.renderer.create_category_embed(category, commands_dict)
        view = await self.create_category_view(category)

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)

    async def handle_command_select(
        self,
        interaction: discord.Interaction,
        command_name: str,
    ) -> None:
        """Handle command selection."""
        command = self.data.find_command(command_name)
        if not command:
            await interaction.followup.send("Command not found.", ephemeral=True)
            return

        self.current_state = HelpState.COMMAND
        self.current_command = command_name
        self.current_command_obj = command

        # For large command groups, initialize pagination and use paginated embed
        if isinstance(command, commands.Group) and (
            command.name in {"jsk", "jishaku"} or len(command.commands) > 15
        ):
            # Initialize pagination for large groups
            if not self.subcommand_pages:
                sorted_cmds = sorted(command.commands, key=lambda x: x.name)
                self._paginate_subcommands(sorted_cmds, preserve_page=False)
            embed = await self._create_paginated_embed()
        else:
            embed = await self.renderer.create_command_embed(command)
        view = await self.create_command_view()

        # Special handling for nested command groups (groups within groups)
        if (
            self.current_command_obj
            and isinstance(self.current_command_obj, commands.Group)
            and self.current_command_obj.commands
        ):
            # Just log nested groups for debugging
            for subcommand in self.current_command_obj.commands:
                if isinstance(subcommand, commands.Group) and subcommand.commands:
                    logger.info(
                        f"Found nested command group: {subcommand.name} with {len(subcommand.commands)} subcommands",
                    )

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)
        else:
            logger.warning("Command selection: No message to update")

    async def handle_subcommand_select(
        self,
        interaction: discord.Interaction,
        subcommand_name: str,
    ) -> None:
        """Handle subcommand selection."""
        # Special handling for the "see all" option in jsk
        if subcommand_name == "_see_all":
            embed = discord.Embed(
                title="Jishaku Help",
                description="For a complete list of Jishaku commands, please use:\n`jsk help`",
                color=0x5865F2,
            )
            if interaction.message:
                await interaction.message.edit(embed=embed)
            return

        # Find the selected subcommand object
        if not self.current_command_obj or not isinstance(
            self.current_command_obj,
            commands.Group,
        ):
            logger.error(
                f"Cannot find parent command object for subcommand {subcommand_name}",
            )
            return

        selected_command = discord.utils.get(
            self.current_command_obj.commands,
            name=subcommand_name,
        )
        if not selected_command:
            logger.error(
                f"Subcommand {subcommand_name} not found in {self.current_command_obj.name}",
            )
            return

        # Check if this subcommand is itself a group with subcommands
        if isinstance(selected_command, commands.Group) and selected_command.commands:
            logger.info(
                f"Selected subcommand '{subcommand_name}' is a group with {len(selected_command.commands)} subcommands",
            )

            # Set this subcommand as the current command to view
            self.current_command = selected_command.name
            self.current_command_obj = selected_command

            # Create a command view for this subcommand group
            embed = await self.renderer.create_command_embed(selected_command)
            view = await self.create_command_view()

            if interaction.message:
                await interaction.message.edit(embed=embed, view=view)

            # Use command state so back button logic will work correctly
            self.current_state = HelpState.COMMAND
            return

        # Normal subcommand handling for non-group subcommands
        self.current_state = HelpState.SUBCOMMAND
        embed = await self.renderer.create_subcommand_embed(
            self.current_command_obj.name,
            selected_command,
        )
        view = await self.create_subcommand_view()

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)
        else:
            logger.warning("Subcommand selection: No message to update")

    async def handle_back_button(self, interaction: discord.Interaction) -> None:
        """Handle back button navigation."""
        if not interaction.message:
            return

        if (
            self.current_state == HelpState.SUBCOMMAND
            and self.current_command
            and self.current_category
            and self.data.command_mapping
            and (
                command := self.data.command_mapping[self.current_category].get(
                    self.current_command,
                )
            )
        ):
            self.current_state = HelpState.COMMAND
            self.current_command_obj = command
            embed = await self.renderer.create_command_embed(command)
            view = await self.create_command_view()
            await interaction.message.edit(embed=embed, view=view)
            return

        if (
            self.current_state == HelpState.COMMAND
            and self.current_command
            and (parent := await self._find_parent_command(self.current_command))
        ):
            parent_name, parent_obj = parent
            logger.info(
                f"Found parent command {parent_name} for {self.current_command}",
            )
            self.current_command = parent_name
            self.current_command_obj = parent_obj
            embed = await self.renderer.create_command_embed(parent_obj)
            view = await self.create_command_view()
            await interaction.message.edit(embed=embed, view=view)
            return

        if self.current_state == HelpState.SUBCOMMAND:
            self.current_state = HelpState.CATEGORY

        self.current_command = None
        self.current_command_obj = None

        if self.current_state == HelpState.COMMAND and self.current_category:
            self.current_state = HelpState.CATEGORY
            categories = await self.data.get_command_categories()
            commands_dict = categories.get(self.current_category, {})
            embed = await self.renderer.create_category_embed(
                self.current_category,
                commands_dict,
            )
            view = await self.create_category_view(self.current_category)
        else:
            self.current_state = HelpState.MAIN
            self.current_category = None
            categories = await self.data.get_command_categories()
            embed = await self.renderer.create_main_embed(categories)
            view = await self.create_main_view()

        await interaction.message.edit(embed=embed, view=view)

    async def handle_next_button(self, interaction: discord.Interaction) -> None:
        """Handle next page navigation."""
        if not self.subcommand_pages:
            logger.warning("Pagination: No subcommand pages available")
            return

        # Read current page directly from self
        current_page = self.current_subcommand_page
        total_pages = len(self.subcommand_pages)

        # Increment the page counter
        if current_page < total_pages - 1:
            self.current_subcommand_page = current_page + 1
        else:
            logger.info(f"Pagination: Already at last page ({current_page})")

        # Update the embed with the new page
        if self.current_command and self.current_command_obj:
            if interaction.message:
                embed = await self._create_paginated_embed()
                view = await self.create_command_view()
                await interaction.message.edit(embed=embed, view=view)
            else:
                logger.warning("Pagination: No message to update")

    async def handle_prev_button(self, interaction: discord.Interaction) -> None:
        """Handle previous page navigation."""
        if not self.subcommand_pages:
            logger.warning("Pagination: No subcommand pages available")
            return

        # Read current page directly from self
        current_page = self.current_subcommand_page

        # Decrement the page counter
        if current_page > 0:
            self.current_subcommand_page = current_page - 1
        else:
            logger.info(f"Pagination: Already at first page ({current_page})")

        # Update the embed with the new page
        if self.current_command and self.current_command_obj:
            if interaction.message:
                embed = await self._create_paginated_embed()
                view = await self.create_command_view()
                await interaction.message.edit(embed=embed, view=view)
            else:
                logger.warning("Pagination: No message to update")
