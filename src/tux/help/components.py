"""UI components for the help command system.

This module contains all the UI components used by the help command, including:
- Base views and components
- Select menus for categories, commands, and subcommands
- Navigation buttons
- Pagination components
"""

from __future__ import annotations

import abc
from typing import Any, Protocol, TypeVar

import discord
from discord.ext import commands

from tux.shared.constants import EMBED_COLORS

# Type aliases
CommandT = TypeVar("CommandT", bound=commands.Command[Any, Any, Any])
GroupT = TypeVar("GroupT", bound=commands.Group[Any, Any, Any])


class HelpCommandProtocol(Protocol):
    """Protocol defining methods a help command must implement."""

    # Navigation state
    current_category: str | None
    current_command: str | None
    current_subcommand_page: int
    subcommand_pages: list[list[commands.Command[Any, Any, Any]]]

    # Navigation handlers
    async def on_category_select(
        self,
        interaction: discord.Interaction,
        category: str,
    ) -> None:
        """Handle category selection from dropdown menu."""
        ...

    async def on_command_select(
        self,
        interaction: discord.Interaction,
        command_name: str,
    ) -> None:
        """Handle command selection from dropdown menu."""
        ...

    async def on_subcommand_select(
        self,
        interaction: discord.Interaction,
        subcommand_name: str,
    ) -> None:
        """Handle subcommand selection from dropdown menu."""
        ...

    async def on_back_button(self, interaction: discord.Interaction) -> None:
        """Handle back navigation button press."""
        ...

    async def on_next_button(self, interaction: discord.Interaction) -> None:
        """Handle next page navigation button press."""
        ...

    async def on_prev_button(self, interaction: discord.Interaction) -> None:
        """Handle previous page navigation button press."""
        ...

    # Context
    @property
    def context(self) -> commands.Context[Any]:
        """Get the Discord context for this help command."""
        ...


class BaseHelpView(discord.ui.View):
    """Base view for all help command navigation."""

    def __init__(self, help_command: HelpCommandProtocol, timeout: int = 180):
        """Initialize the base help view.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this view belongs to.
        timeout : int, optional
            View timeout in seconds (default 180).
        """
        super().__init__(timeout=timeout)
        self.help_command = help_command
        self.author = help_command.context.author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Ensure only the invoker can interact with this view.

        Returns
        -------
        bool
            True if the interaction user is the author, False otherwise.
        """
        if interaction.user != self.author:
            await interaction.response.send_message(
                "You can't interact with others help menus!",
                ephemeral=True,
            )
            return False
        return True


class BaseSelectMenu(discord.ui.Select[BaseHelpView]):
    """Base class for help selection menus."""

    def __init__(
        self,
        help_command: HelpCommandProtocol,
        options: list[discord.SelectOption],
        placeholder: str,
    ):
        """Initialize the base select menu.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this menu belongs to.
        options : list[discord.SelectOption]
            List of options for the select menu.
        placeholder : str
            Placeholder text for the select menu.
        """
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )
        self.help_command = help_command

    @abc.abstractmethod
    async def handle_select(
        self,
        interaction: discord.Interaction,
        selected_value: str,
    ) -> None:
        """Handle a selection from this menu."""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle the callback when an option is selected."""
        await interaction.response.defer()
        value = self.values[0]
        await self.handle_select(interaction, value)


class BaseButton(discord.ui.Button[BaseHelpView]):
    """Base class for help navigation buttons."""

    def __init__(
        self,
        help_command: HelpCommandProtocol,
        style: discord.ButtonStyle,
        label: str,
        emoji: str,
        custom_id: str,
        disabled: bool = False,
    ):
        """Initialize the base button.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this button belongs to.
        style : discord.ButtonStyle
            The button style (primary, secondary, success, danger, link).
        label : str
            The button label text.
        emoji : str
            The button emoji.
        custom_id : str
            Unique identifier for the button.
        disabled : bool, optional
            Whether the button is disabled (default False).
        """
        super().__init__(
            style=style,
            label=label,
            emoji=emoji,
            custom_id=custom_id,
            disabled=disabled,
        )
        self.help_command = help_command

    @abc.abstractmethod
    async def handle_click(self, interaction: discord.Interaction) -> None:
        """Handle a click on this button."""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle the callback when the button is clicked."""
        await interaction.response.defer()
        await self.handle_click(interaction)


# Concrete UI Components


class CategorySelectMenu(BaseSelectMenu):
    """Select menu for choosing a command category."""

    async def handle_select(
        self,
        interaction: discord.Interaction,
        selected_value: str,
    ) -> None:
        """Handle when a category is selected."""
        await self.help_command.on_category_select(interaction, selected_value)


class CommandSelectMenu(BaseSelectMenu):
    """Select menu for choosing a command within a category."""

    async def handle_select(
        self,
        interaction: discord.Interaction,
        selected_value: str,
    ) -> None:
        """Handle when a command is selected."""
        await self.help_command.on_command_select(interaction, selected_value)


class SubcommandSelectMenu(BaseSelectMenu):
    """Select menu for choosing a subcommand within a command group."""

    async def handle_select(
        self,
        interaction: discord.Interaction,
        selected_value: str,
    ) -> None:
        """Handle when a subcommand is selected."""
        await self.help_command.on_subcommand_select(interaction, selected_value)


class BackButton(BaseButton):
    """Button for navigating back to the previous page."""

    def __init__(self, help_command: HelpCommandProtocol):
        """Initialize the back navigation button.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this button belongs to.
        """
        super().__init__(
            help_command=help_command,
            style=discord.ButtonStyle.secondary,
            label="Back",
            emoji="↩️",
            custom_id="back_button",
        )

    async def handle_click(self, interaction: discord.Interaction) -> None:
        """Handle when the back button is clicked."""
        await self.help_command.on_back_button(interaction)


class CloseButton(discord.ui.Button[BaseHelpView]):
    """Button for closing the help menu."""

    def __init__(self):
        """Initialize the close button for dismissing the help menu."""
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Close",
            emoji="✖️",
            custom_id="close_button",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle when the close button is clicked."""
        if interaction.message:
            await interaction.message.delete()


class PaginationButton(BaseButton):
    """Base class for pagination buttons."""

    def __init__(
        self,
        help_command: HelpCommandProtocol,
        label: str,
        emoji: str,
        custom_id: str,
        is_next: bool,
    ):
        """Initialize the pagination button.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this button belongs to.
        label : str
            The button label text.
        emoji : str
            The button emoji.
        custom_id : str
            Unique identifier for the button.
        is_next : bool
            Whether this is a "next" button (True) or "previous" button (False).
        """
        # Determine if button should be disabled based on current page
        current_page = help_command.current_subcommand_page
        disabled = False
        if is_next:
            total_pages = len(help_command.subcommand_pages)
            disabled = current_page >= total_pages - 1
        else:  # Previous button
            disabled = current_page <= 0

        super().__init__(
            help_command=help_command,
            style=discord.ButtonStyle.primary,
            label=label,
            emoji=emoji,
            custom_id=f"{custom_id}_{current_page}",
            disabled=disabled,
        )
        self.is_next = is_next


class NextButton(PaginationButton):
    """Button for navigating to the next page of subcommands."""

    def __init__(self, help_command: HelpCommandProtocol):
        """Initialize the next page navigation button.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this button belongs to.
        """
        super().__init__(
            help_command=help_command,
            label="Next",
            emoji="▶️",
            custom_id="next_button",
            is_next=True,
        )

    async def handle_click(self, interaction: discord.Interaction) -> None:
        """Handle when the next button is clicked."""
        await self.help_command.on_next_button(interaction)


class PrevButton(PaginationButton):
    """Button for navigating to the previous page of subcommands."""

    def __init__(self, help_command: HelpCommandProtocol):
        """Initialize the previous page navigation button.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this button belongs to.
        """
        super().__init__(
            help_command=help_command,
            label="Previous",
            emoji="◀️",
            custom_id="prev_button",
            is_next=False,
        )

    async def handle_click(self, interaction: discord.Interaction) -> None:
        """Handle when the previous button is clicked."""
        await self.help_command.on_prev_button(interaction)


class HelpView(BaseHelpView):
    """Main view for the help command with standard navigation."""


class DirectHelpView(BaseHelpView):
    """View for paginated direct help commands with previous/next buttons."""

    def __init__(
        self,
        help_command: HelpCommandProtocol,
        group: commands.Group[Any, Any, Any],
        pages: list[list[commands.Command[Any, Any, Any]]],
    ):
        """Initialize the direct help view with pagination.

        Parameters
        ----------
        help_command : HelpCommandProtocol
            The help command instance this view belongs to.
        group : commands.Group[Any, Any, Any]
            The command group to display help for.
        pages : list[list[commands.Command[Any, Any, Any]]]
            Pre-paginated list of commands for navigation.
        """
        super().__init__(help_command)
        self.group = group
        self.current_page = 0
        self.pages = pages

        # Add navigation buttons
        self.prev_button = discord.ui.Button[BaseHelpView](
            label="Previous",
            style=discord.ButtonStyle.primary,
            emoji="◀️",
            custom_id="prev_page",
            disabled=True,
        )
        self.prev_button.callback = self.prev_button_callback
        self.add_item(self.prev_button)

        self.next_button = discord.ui.Button[BaseHelpView](
            label="Next",
            style=discord.ButtonStyle.primary,
            emoji="▶️",
            custom_id="next_page",
            disabled=len(self.pages) <= 1,
        )
        self.next_button.callback = self.next_button_callback
        self.add_item(self.next_button)

        # Add close button
        close_button = discord.ui.Button[BaseHelpView](
            label="Close",
            style=discord.ButtonStyle.danger,
            emoji="✖️",
            custom_id="close_help",
        )
        close_button.callback = self.close_button_callback
        self.add_item(close_button)

    async def get_embed(self) -> discord.Embed:
        """
        Get the embed for the current page.

        Returns
        -------
        discord.Embed
            The embed for the current subcommand page.
        """
        # Get prefix from the context
        prefix = self.help_command.context.clean_prefix

        # Format help text with proper quoting for all lines
        help_text = self.group.help or "No documentation available."
        formatted_help = "\n".join(f"> {line}" for line in help_text.split("\n"))

        embed = discord.Embed(
            title=f"{prefix}{self.group.qualified_name}",
            description=formatted_help,
            color=EMBED_COLORS["DEFAULT"],
        )

        # Add basic command info
        embed.add_field(
            name="Usage",
            value=f"`{prefix}{self.group.qualified_name} <subcommand>`",
            inline=False,
        )

        if self.group.aliases:
            embed.add_field(
                name="Aliases",
                value=f"`{', '.join(self.group.aliases)}`",
                inline=False,
            )

        # If we have pages
        if self.pages:
            current_page_cmds = self.pages[self.current_page]
            page_num = self.current_page + 1
            total_pages = len(self.pages)

            embed.add_field(
                name=f"Subcommands (Page {page_num}/{total_pages})",
                value=f"This command has {sum(len(page) for page in self.pages)} subcommands:",
                inline=False,
            )

            # Add each subcommand with a non-inline field
            for cmd in current_page_cmds:
                embed.add_field(
                    name=cmd.name,
                    value=f"> {cmd.short_doc or 'No description'}",
                    inline=False,
                )

        return embed

    async def prev_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle previous page button press."""
        await interaction.response.defer()

        if self.current_page > 0:
            self.current_page -= 1

            # Update button states
            self.prev_button.disabled = self.current_page == 0
            self.next_button.disabled = False

            embed = await self.get_embed()
            if interaction.message:
                await interaction.message.edit(embed=embed, view=self)

    async def next_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle next page button press."""
        await interaction.response.defer()

        if self.current_page < len(self.pages) - 1:
            self.current_page += 1

            # Update button states
            self.prev_button.disabled = False
            self.next_button.disabled = self.current_page == len(self.pages) - 1

            embed = await self.get_embed()
            if interaction.message:
                await interaction.message.edit(embed=embed, view=self)

    async def close_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle close button press."""
        if interaction.message:
            await interaction.message.delete()
