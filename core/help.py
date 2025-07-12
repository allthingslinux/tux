"""
Help command system for Tux.

This module implements an interactive help command with support for:
- Category browsing
- Command details
- Subcommand navigation
- Pagination for large command groups
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum, auto
from typing import Any, TypeVar, get_type_hints

import discord
from discord import SelectOption
from discord.ext import commands
from loguru import logger

from core.config import CONFIG
from core.env import get_current_env
from core.ui.embeds import EmbedCreator
from core.ui.help_components import (
    BackButton,
    CategorySelectMenu,
    CloseButton,
    CommandSelectMenu,
    DirectHelpView,
    HelpView,
    NextButton,
    PrevButton,
    SubcommandSelectMenu,
)
from core.utils.constants import CONST
from core.utils.help_utils import (
    create_cog_category_mapping,
    format_multiline_description,
    paginate_items,
    truncate_description,
)

# Type variables for command generics
CommandT = TypeVar("CommandT", bound=commands.Command[Any, Any, Any])


class HelpState(Enum):
    """Navigation states for the help command."""

    MAIN = auto()
    CATEGORY = auto()
    COMMAND = auto()
    SUBCOMMAND = auto()


class TuxHelp(commands.HelpCommand):
    """
    Interactive help command for Tux.

    This class implements an interactive help command with support for category browsing,
    command details, subcommand navigation, and pagination for large command groups.

    Attributes
    ----------
    _prefix_cache : dict[int or None, str]
        Cache for storing guild-specific command prefixes.
    _category_cache : dict[str, dict[str, str]]
        Cache for storing command categories.
    current_category : str or None
        Currently selected category.
    current_command : str or None
        Currently selected command.
    current_page : HelpState
        Current page state.
    current_subcommand_page : int
        Current page index for subcommands.
    message : discord.Message or None
        Last message context.
    command_mapping : dict[str, dict[str, commands.Command]] or None
        Mapping of command names to command objects.
    current_command_obj : commands.Command or None
        The currently active command object.
    subcommand_pages : list[list[commands.Command]]
        List of pages containing subcommands.
    """

    def __init__(self) -> None:
        """
        Initialize the help command with necessary attributes.

        Notes
        -----
        This also initializes caches and state tracking for the help command.
        """
        super().__init__(
            command_attrs={
                "help": "Lists all commands and sub-commands.",
                "aliases": ["h", "commands"],
                "usage": "$help <command> or <sub-command>",
            },
        )

        # Caches
        self._prefix_cache: dict[int | None, str] = {}
        self._category_cache: dict[str, dict[str, str]] = {}

        # State tracking
        self.current_category: str | None = None
        self.current_command: str | None = None
        self.current_page = HelpState.MAIN
        self.current_subcommand_page: int = 0

        # Message and command tracking
        self.message: discord.Message | None = None
        self.command_mapping: dict[str, dict[str, commands.Command[Any, Any, Any]]] | None = None
        self.current_command_obj: commands.Command[Any, Any, Any] | None = None
        self.subcommand_pages: list[list[commands.Command[Any, Any, Any]]] = []

    # Prefix and embed utilities

    async def _get_prefix(self) -> str:
        """
        Get the guild-specific command prefix.

        Returns
        -------
        str
            The command prefix for the current guild.
        """
        guild_id = self.context.guild.id if self.context.guild else None

        if guild_id not in self._prefix_cache:
            # Fetch and cache the prefix specific to the guild
            self._prefix_cache[guild_id] = self.context.clean_prefix or CONFIG.DEFAULT_PREFIX

        return self._prefix_cache[guild_id]

    def _embed_base(self, title: str, description: str | None = None) -> discord.Embed:
        """
        Create a base embed with consistent styling.

        Parameters
        ----------
        title : str
            The embed title.
        description : str or None, optional
            The embed description (default is None).

        Returns
        -------
        discord.Embed
            A styled embed object.
        """
        return discord.Embed(
            title=title,
            description=description,
            color=CONST.EMBED_COLORS["DEFAULT"],
        )

    # Flag formatting methods

    def _format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        """
        Format the details of command flags.

        Parameters
        ----------
        command : commands.Command
            The command for which to format the flags.

        Returns
        -------
        str
            Formatted string of flag details.
        """
        flag_details: list[str] = []

        try:
            type_hints = get_type_hints(command.callback)
        except Exception:
            return ""

        for param_annotation in type_hints.values():
            if not isinstance(param_annotation, type) or not issubclass(param_annotation, commands.FlagConverter):
                continue

            for flag in param_annotation.__commands_flags__.values():
                flag_str = self._format_flag_name(flag)
                if flag.aliases and not getattr(flag, "positional", False):
                    flag_str += f" ({', '.join(flag.aliases)})"
                flag_str += f"\n\t{flag.description or 'No description provided'}"
                if flag.default is not discord.utils.MISSING:
                    flag_str += f"\n\tDefault: {flag.default}"
                flag_details.append(flag_str)

        return "\n\n".join(flag_details)

    @staticmethod
    def _format_flag_name(flag: commands.Flag) -> str:
        """
        Format a flag name based on its properties.

        Parameters
        ----------
        flag : commands.Flag
            The flag to format.

        Returns
        -------
        str
            Formatted flag name string.
        """
        if getattr(flag, "positional", False):
            return f"<{flag.name}>" if flag.required else f"[{flag.name}]"
        return f"-{flag.name}" if flag.required else f"[-{flag.name}]"

    # Command usage and fields

    def _generate_default_usage(self, command: commands.Command[Any, Any, Any]) -> str:
        """
        Generate a default usage string for a command.

        Parameters
        ----------
        command : commands.Command
            The command for which to generate usage.

        Returns
        -------
        str
            Formatted usage string.
        """
        signature = command.signature.strip()
        if not signature:
            return command.qualified_name

        # Format the signature to look more like Discord's native format
        # Replace things like [optional] with <optional>
        formatted_signature = signature.replace("[", "<").replace("]", ">")
        return f"{command.qualified_name} {formatted_signature}"

    async def _add_command_help_fields(self, embed: discord.Embed, command: commands.Command[Any, Any, Any]) -> None:
        """
        Add usage and alias fields to the command embed.

        Parameters
        ----------
        embed : discord.Embed
            The embed object to add fields to.
        command : commands.Command
            The command for which to add help fields.
        """
        prefix = await self._get_prefix()
        usage = command.usage or self._generate_default_usage(command)
        embed.add_field(name="Usage", value=f"`{prefix}{usage}`", inline=False)
        embed.add_field(
            name="Aliases",
            value=(f"`{', '.join(command.aliases)}`" if command.aliases else "No aliases"),
            inline=False,
        )

    @staticmethod
    def _add_command_field(embed: discord.Embed, command: commands.Command[Any, Any, Any], prefix: str) -> None:
        """
        Add a command as a field in the embed.

        Parameters
        ----------
        embed : discord.Embed
            The embed object to update.
        command : commands.Command
            The command to add.
        prefix : str
            The command prefix.
        """
        command_aliases = ", ".join(command.aliases) if command.aliases else "No aliases"
        embed.add_field(
            name=f"{prefix}{command.qualified_name} ({command_aliases})",
            value=f"> {command.short_doc or 'No documentation summary'}",
            inline=False,
        )

    # Category and command mapping

    async def _get_command_categories(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, commands.Command[Any, Any, Any]]]]:
        """
        Retrieve command categories and mapping.

        Parameters
        ----------
        mapping : Mapping[commands.Cog | None, list[commands.Command]]
            Mapping of cogs to their commands.

        Returns
        -------
        tuple
            A tuple containing:
            - dict: Category cache mapping category names to command details.
            - dict: Command mapping of categories to command objects.
        """
        if self._category_cache:
            return self._category_cache, self.command_mapping or {}

        self._category_cache, self.command_mapping = create_cog_category_mapping(mapping)
        return self._category_cache, self.command_mapping

    # Pagination methods

    def _paginate_subcommands(
        self,
        commands_list: list[commands.Command[Any, Any, Any]],
        preserve_page: bool = False,
    ) -> None:
        """
        Split subcommands into pages for pagination.

        Parameters
        ----------
        commands_list : list of commands.Command
            List of commands to paginate.
        preserve_page : bool, optional
            If True, preserve the current page index; otherwise, reset to first page.
        """
        current_page = self.current_subcommand_page if preserve_page else 0
        self.subcommand_pages = paginate_items(commands_list, 10)

        # Restore or reset page counter
        if preserve_page:
            # Make sure the page index is valid for the new pagination
            self.current_subcommand_page = min(current_page, len(self.subcommand_pages) - 1)
        else:
            # Reset to first page when paginating
            self.current_subcommand_page = 0

    def _find_command(self, command_name: str) -> commands.Command[Any, Any, Any] | None:
        """
        Find and return the command object for a given command name.

        Parameters
        ----------
        command_name : str
            The name of the command to search for.

        Returns
        -------
        commands.Command or None
            The command object if found; otherwise, None.
        """
        if (
            self.current_category
            and self.command_mapping
            and (found := self.command_mapping[self.current_category].get(command_name))
        ):
            return found
        if (
            self.current_command_obj
            and isinstance(self.current_command_obj, commands.Group)
            and (found := discord.utils.get(self.current_command_obj.commands, name=command_name))
        ):
            return found
        if self.command_mapping:
            for category_commands in self.command_mapping.values():
                for cmd in category_commands.values():
                    if isinstance(cmd, commands.Group) and (
                        found := discord.utils.get(cmd.commands, name=command_name)
                    ):
                        return found
        return None

    def _find_parent_command(self, subcommand_name: str) -> tuple[str, commands.Command[Any, Any, Any]] | None:
        """
        Find the parent command for a given subcommand.

        Parameters
        ----------
        subcommand_name : str
            The subcommand name to find the parent for.

        Returns
        -------
        tuple of (str, commands.Command) or None
            A tuple containing the parent command name and object, or None if not found.
        """
        if self.command_mapping:
            for category_commands in self.command_mapping.values():
                for parent_name, cmd in category_commands.items():
                    if isinstance(cmd, commands.Group) and discord.utils.get(cmd.commands, name=subcommand_name):
                        return parent_name, cmd
        return None

    # UI creation methods

    async def _create_category_options(self) -> list[discord.SelectOption]:
        """
        Create select options for category selection.

        Returns
        -------
        list of discord.SelectOption
            A list of select options for available command categories.
        """
        category_emoji_map = {
            "info": "🔍",
            "moderation": "🛡",
            "utility": "🔧",
            "snippets": "📝",
            "admin": "👑",
            "fun": "🎉",
            "levels": "📈",
            "services": "🔌",
            "guild": "🏰",
            "tools": "🛠",
        }

        options: list[discord.SelectOption] = []
        for category in self._category_cache:
            if any(self._category_cache[category].values()):
                emoji = category_emoji_map.get(category, "❓")
                options.append(
                    discord.SelectOption(
                        label=category.capitalize(),
                        value=category,
                        emoji=emoji,
                        description=f"View {category.capitalize()} commands",
                    ),
                )

        return sorted(options, key=lambda o: o.label)

    async def _create_command_options(self, category: str) -> list[discord.SelectOption]:
        """
        Create select options for commands within a specified category.

        Parameters
        ----------
        category : str
            The category for which to create command options.

        Returns
        -------
        list of discord.SelectOption
            A list of select options corresponding to the commands in the category.
        """
        options: list[discord.SelectOption] = []

        if self.command_mapping and category in self.command_mapping:
            for cmd_name, cmd in self.command_mapping[category].items():
                description = truncate_description(cmd.short_doc or "No description")

                # Add an indicator for group commands
                is_group = isinstance(cmd, commands.Group) and len(cmd.commands) > 0
                label = f"{cmd_name}{'†' if is_group else ''}"

                options.append(SelectOption(label=label, value=cmd_name, description=description))

        else:
            logger.warning(f"No commands found for category {category}")

        return sorted(options, key=lambda o: o.label)

    async def _create_subcommand_options(self, command: commands.Group[Any, Any, Any]) -> list[SelectOption]:
        """
        Create select options for subcommands within a command group.

        Parameters
        ----------
        command : commands.Group
            The command group for which to create subcommand options.

        Returns
        -------
        list of discord.SelectOption
            A list of select options for the subcommands.
        """
        # Special handling for jishaku to prevent loading all subcommands
        if command.name not in {"jsk", "jishaku"}:
            # Normal handling for other command groups
            return [
                SelectOption(
                    label=subcmd.name,
                    value=subcmd.name,
                    description=truncate_description(subcmd.short_doc or "No description"),
                )
                for subcmd in sorted(command.commands, key=lambda x: x.name)
            ]
        # Only include a few important jishaku commands
        essential_subcmds = ["py", "shell", "cat", "curl", "pip", "git", "help"]

        subcommand_options: list[SelectOption] = []
        for subcmd_name in essential_subcmds:
            if subcmd := discord.utils.get(command.commands, name=subcmd_name):
                description = truncate_description(subcmd.short_doc or "No description")
                subcommand_options.append(SelectOption(label=subcmd.name, value=subcmd.name, description=description))

        # Add an option to suggest using jsk help
        subcommand_options.append(
            SelectOption(
                label="See all commands",
                value="_see_all",
                description="Use jsk help command for complete list",
            ),
        )

        return subcommand_options

    # Embed creation methods

    async def _create_main_embed(self) -> discord.Embed:
        """
        Create the main help embed.

        Returns
        -------
        discord.Embed
            The main help embed to be displayed.
        """
        if CONFIG.BOT_NAME != "Tux":
            logger.info("Bot name is not Tux, using different help message.")
            embed = self._embed_base(
                "Hello! Welcome to the help command.",
                f"{CONFIG.BOT_NAME} is a self-hosted instance of Tux. The bot is written in Python using discord.py.\n\nIf you enjoy using {CONFIG.BOT_NAME}, consider contributing to the original project.",
            )
        else:
            embed = self._embed_base(
                "Hello! Welcome to the help command.",
                "Tux is an all-in-one bot by the All Things Linux Discord server. The bot is written in Python using discord.py, and we are actively seeking contributors.",
            )

        await self._add_bot_help_fields(embed)
        return embed

    async def _create_category_embed(self, category: str) -> discord.Embed:
        """
        Create an embed for a specific category.

        Parameters
        ----------
        category : str
            The category name.

        Returns
        -------
        discord.Embed
            The embed displaying commands for the category.
        """
        prefix = await self._get_prefix()
        embed = self._embed_base(f"{category.capitalize()} Commands")

        embed.set_footer(
            text="Select a command from the dropdown to see details.",
        )

        sorted_commands = sorted(self._category_cache[category].items())
        description = "\n".join(f"**`{prefix}{cmd}`** | {command_list}" for cmd, command_list in sorted_commands)
        embed.description = description

        return embed

    async def _create_command_embed(self, command_name: str) -> discord.Embed:
        """
        Create an embed for a specific command.

        Parameters
        ----------
        command_name : str
            The name of the command.

        Returns
        -------
        discord.Embed
            The embed with command details.
        """
        command = self._find_command(command_name)
        if not command:
            logger.error(
                f"Command '{command_name}' not found. Category: {self.current_category}, Current command: {self.current_command}",
            )
            return self._embed_base("Error", "Command not found")

        # Store the current command object for reference
        self.current_command_obj = command
        self.current_command = command_name

        prefix = await self._get_prefix()
        help_text = format_multiline_description(command.help)
        embed = self._embed_base(
            title=f"{prefix}{command.qualified_name}",
            description=help_text,
        )

        # Add command fields
        await self._add_command_help_fields(embed, command)

        # Add flag details if present
        if flag_details := self._format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        # Add subcommands section if this is a group
        if isinstance(command, commands.Group) and command.commands:
            sorted_cmds = sorted(command.commands, key=lambda x: x.name)

            if nested_groups := [cmd for cmd in sorted_cmds if isinstance(cmd, commands.Group) and cmd.commands]:
                nested_groups_text = "\n".join(
                    f"• `{g.name}` - {truncate_description(g.short_doc or 'No description')} ({len(g.commands)} subcommands)"
                    for g in nested_groups
                )
                embed.add_field(
                    name="Nested Command Groups",
                    value=(
                        f"This command has the following subcommand groups:\n\n{nested_groups_text}\n\nSelect a group command to see its subcommands."
                    ),
                    inline=False,
                )

            self._paginate_subcommands(sorted_cmds, preserve_page=True)

            # For large command groups like JSK, show paginated view
            if command.name in {"jsk", "jishaku"} or len(sorted_cmds) > 15:
                valid_page = self.subcommand_pages and 0 <= self.current_subcommand_page < len(self.subcommand_pages)
                current_page_cmds = (
                    self.subcommand_pages[self.current_subcommand_page] if valid_page else sorted_cmds[:10]
                )
                if not valid_page:
                    logger.warning(
                        f"Invalid page index: {self.current_subcommand_page}, pages: {len(self.subcommand_pages)}",
                    )

                subcommands_list = "\n".join(
                    f"• `{c.name}{'†' if isinstance(c, commands.Group) and c.commands else ''}` - {c.short_doc or 'No description'}"
                    for c in current_page_cmds
                )

                total_count = len(sorted_cmds)
                page_num = self.current_subcommand_page + 1
                total_pages = len(self.subcommand_pages) or 1

                embed.add_field(
                    name=f"Subcommands (Page {page_num}/{total_pages})",
                    value=(
                        f"This command has {total_count} subcommands:\n\n{subcommands_list}\n\nUse the navigation buttons to browse all subcommands."
                    ),
                    inline=False,
                )
            else:
                subcommands_list = "\n".join(
                    f"• `{c.name}{'†' if isinstance(c, commands.Group) and c.commands else ''}` - {c.short_doc or 'No description'}"
                    for c in sorted_cmds
                )
                embed.add_field(
                    name="Subcommands",
                    value=(
                        f"This command group has the following subcommands:\n\n{subcommands_list}\n\nSelect a subcommand from the dropdown to see more details."
                    ),
                    inline=False,
                )
        return embed

    async def _create_subcommand_embed(self, subcommand_name: str) -> discord.Embed:
        """
        Create an embed for a specific subcommand.

        Parameters
        ----------
        subcommand_name : str
            The name of the subcommand.

        Returns
        -------
        discord.Embed
            The embed with subcommand details.
        """
        if not self.current_command_obj or not isinstance(self.current_command_obj, commands.Group):
            return self._embed_base("Error", "Parent command not found")

        # Find the subcommand
        subcommand = discord.utils.get(self.current_command_obj.commands, name=subcommand_name)
        if not subcommand:
            return self._embed_base("Error", "Subcommand not found")

        prefix = await self._get_prefix()

        # Format help text with proper quoting
        help_text = format_multiline_description(subcommand.help)

        embed = self._embed_base(
            title=f"{prefix}{subcommand.qualified_name}",
            description=help_text,
        )

        await self._add_command_help_fields(embed, subcommand)

        if flag_details := self._format_flag_details(subcommand):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        return embed

    async def _add_bot_help_fields(self, embed: discord.Embed) -> None:
        """
        Add additional help information about the bot to the embed.

        Parameters
        ----------
        embed : discord.Embed
            The embed to which the help information will be added.
        """
        prefix = await self._get_prefix()

        embed.add_field(
            name="How to Use",
            value=f"Most commands are hybrid meaning they can be used via prefix `{prefix}` OR slash `/`. Commands strictly available via `/` are not listed in the help menu.",
            inline=False,
        )
        embed.add_field(
            name="Command Help",
            value="Select a category from the dropdown, then select a command to view details.",
            inline=False,
        )
        embed.add_field(
            name="Flag Help",
            value=f"Flags in `[]` are optional. Most flags have aliases that can be used.\n> e.g. `{prefix}ban @user spamming` or `{prefix}b @user spam -silent true`",
            inline=False,
        )
        embed.add_field(
            name="Support Server",
            value="-# [Need support? Join Server](https://discord.gg/gpmSjcjQxg)",
            inline=True,
        )
        embed.add_field(
            name="GitHub Repository",
            value="-# [Help contribute! View Repo](https://github.com/allthingslinux/tux)",
            inline=True,
        )

        bot_name_display = "Tux" if CONFIG.BOT_NAME == "Tux" else f"{CONFIG.BOT_NAME} (Tux)"
        environment = get_current_env()
        owner_info = f"Bot Owner: <@{CONFIG.BOT_OWNER_ID}>" if not CONFIG.HIDE_BOT_OWNER and CONFIG.BOT_OWNER_ID else ""

        embed.add_field(
            name="Bot Instance",
            value=f"-# Running {bot_name_display} v `{CONFIG.BOT_VERSION}` in `{environment}` mode"
            + (f"\n-# {owner_info}" if owner_info else ""),
            inline=False,
        )

    # View creation methods

    async def _create_main_view(self) -> HelpView:
        """
        Create the main help view with category selection.

        Returns
        -------
        HelpView
            A view containing category selection and a close button.
        """
        view = HelpView(self)

        # Add category select
        category_options = await self._create_category_options()
        category_select = CategorySelectMenu(self, category_options, "Select a category")
        view.add_item(category_select)

        # Add close button
        view.add_item(CloseButton())

        return view

    async def _create_category_view(self, category: str) -> HelpView:
        """
        Create a view for a specific category with command selection.

        Parameters
        ----------
        category : str
            The category name.

        Returns
        -------
        HelpView
            The view for the selected category.
        """
        view = HelpView(self)

        # Add command select for this category
        command_options = await self._create_command_options(category)
        command_select = CommandSelectMenu(self, command_options, f"Select a {category} command")
        view.add_item(command_select)

        # Add back button and close button
        view.add_item(BackButton(self))
        view.add_item(CloseButton())

        return view

    async def _create_command_view(self) -> HelpView:
        """
        Create a view for a command with navigation options.

        Returns
        -------
        HelpView
            A view for navigating command details.
        """
        view = HelpView(self)

        # Add back button first
        view.add_item(BackButton(self))

        # If this is a command group, handle navigation
        if (
            self.current_command_obj
            and isinstance(self.current_command_obj, commands.Group)
            and len(self.current_command_obj.commands) > 0
        ):
            sorted_cmds = sorted(self.current_command_obj.commands, key=lambda x: x.name)

            # For large command groups like JSK, use pagination buttons and add a select menu for the current page
            if self.current_command_obj.name in {"jsk", "jishaku"} or len(sorted_cmds) > 15:
                if not self.subcommand_pages:
                    self._paginate_subcommands(sorted_cmds, preserve_page=True)

                if len(self.subcommand_pages) > 1:
                    view.add_item(PrevButton(self))
                    view.add_item(NextButton(self))

                valid_page = self.subcommand_pages and 0 <= self.current_subcommand_page < len(self.subcommand_pages)
                current_page_cmds = self.subcommand_pages[self.current_subcommand_page] if valid_page else []
                if not valid_page:
                    logger.warning(
                        f"Invalid page index: {self.current_subcommand_page}, pages: {len(self.subcommand_pages)}",
                    )

                if jsk_select_options := [
                    discord.SelectOption(
                        label=cmd.name,
                        value=cmd.name,
                        description=truncate_description(cmd.short_doc or "No description"),
                    )
                    for cmd in current_page_cmds
                ]:
                    jsk_select = CommandSelectMenu(self, jsk_select_options, "Select a command")
                    view.add_item(jsk_select)
            else:
                logger.info(
                    f"Creating dropdown for command group: {self.current_command_obj.name} with {len(sorted_cmds)} subcommands",
                )

                if subcommand_options := await self._create_subcommand_options(self.current_command_obj):
                    subcommand_select = SubcommandSelectMenu(self, subcommand_options, "Select a subcommand")
                    view.add_item(subcommand_select)

                if nested_groups := [cmd for cmd in sorted_cmds if isinstance(cmd, commands.Group) and cmd.commands]:
                    for group_cmd in nested_groups:
                        logger.info(
                            f"Adding nested group handling for {group_cmd.name} with {len(group_cmd.commands)} subcommands",
                        )

        # Add close button last
        view.add_item(CloseButton())

        return view

    async def _create_subcommand_view(self) -> HelpView:
        """
        Create a view for a subcommand with back navigation.

        Returns
        -------
        HelpView
            A view for displaying subcommand details.
        """
        view = HelpView(self)

        # Add back buttons and close button
        view.add_item(BackButton(self))
        view.add_item(CloseButton())

        return view

    # Event handlers for UI components

    async def on_category_select(self, interaction: discord.Interaction, category: str) -> None:
        """
        Handle the event when a category is selected.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event.
        category : str
            The selected category.
        """
        self.current_category = category
        self.current_page = HelpState.CATEGORY

        embed = await self._create_category_embed(category)
        view = await self._create_category_view(category)

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)

    async def on_command_select(self, interaction: discord.Interaction, command_name: str) -> None:
        """
        Handle the event when a command is selected.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event.
        command_name : str
            The selected command.
        """
        self.current_page = HelpState.COMMAND

        embed = await self._create_command_embed(command_name)
        view = await self._create_command_view()

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

    async def on_subcommand_select(self, interaction: discord.Interaction, subcommand_name: str) -> None:
        """
        Handle the event when a subcommand is selected.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event.
        subcommand_name : str
            The selected subcommand.
        """
        # Special handling for the "see all" option in jsk
        if subcommand_name == "_see_all":
            embed = discord.Embed(
                title="Jishaku Help",
                description="For a complete list of Jishaku commands, please use:\n`jsk help`",
                color=CONST.EMBED_COLORS["INFO"],
            )
            if interaction.message:
                await interaction.message.edit(embed=embed)
            return

        # Find the selected subcommand object
        if not self.current_command_obj or not isinstance(self.current_command_obj, commands.Group):
            logger.error(f"Cannot find parent command object for subcommand {subcommand_name}")
            return

        selected_command = discord.utils.get(self.current_command_obj.commands, name=subcommand_name)
        if not selected_command:
            logger.error(f"Subcommand {subcommand_name} not found in {self.current_command_obj.name}")
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
            embed = await self._create_command_embed(selected_command.name)
            view = await self._create_command_view()

            if interaction.message:
                await interaction.message.edit(embed=embed, view=view)

            # Use command state so back button logic will work correctly
            self.current_page = HelpState.COMMAND
            return

        # Normal subcommand handling for non-group subcommands
        self.current_page = HelpState.SUBCOMMAND
        embed = await self._create_subcommand_embed(subcommand_name)
        view = await self._create_subcommand_view()

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)
        else:
            logger.warning("Subcommand selection: No message to update")

    async def on_back_button(self, interaction: discord.Interaction) -> None:
        """
        Handle the event when the back button is clicked.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event.
        """
        if not interaction.message:
            return

        if (
            self.current_page == HelpState.SUBCOMMAND
            and self.current_command
            and self.current_category
            and self.command_mapping
            and (command := self.command_mapping[self.current_category].get(self.current_command))
        ):
            self.current_page = HelpState.COMMAND
            self.current_command_obj = command
            embed = await self._create_command_embed(self.current_command)
            view = await self._create_command_view()
            await interaction.message.edit(embed=embed, view=view)
            return

        if (
            self.current_page == HelpState.COMMAND
            and self.current_command
            and (parent := self._find_parent_command(self.current_command))
        ):
            parent_name, parent_obj = parent
            logger.info(f"Found parent command {parent_name} for {self.current_command}")
            self.current_command = parent_name
            self.current_command_obj = parent_obj
            embed = await self._create_command_embed(parent_name)
            view = await self._create_command_view()
            await interaction.message.edit(embed=embed, view=view)
            return

        if self.current_page == HelpState.SUBCOMMAND:
            self.current_page = HelpState.CATEGORY

        self.current_command = None
        self.current_command_obj = None

        if self.current_page == HelpState.COMMAND and self.current_category:
            self.current_page = HelpState.CATEGORY
            embed = await self._create_category_embed(self.current_category)
            view = await self._create_category_view(self.current_category)
        else:
            self.current_page = HelpState.MAIN
            self.current_category = None
            embed = await self._create_main_embed()
            view = await self._create_main_view()

        await interaction.message.edit(embed=embed, view=view)

    async def on_next_button(self, interaction: discord.Interaction) -> None:
        """
        Handle navigation to the next page of subcommands.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event.
        """
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
        if self.current_command:
            if interaction.message:
                embed = await self._create_command_embed(self.current_command)
                view = await self._create_command_view()
                await interaction.message.edit(embed=embed, view=view)
            else:
                logger.warning("Pagination: No message to update")

    async def on_prev_button(self, interaction: discord.Interaction) -> None:
        """
        Handle navigation to the previous page of subcommands.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction event.
        """
        if not self.subcommand_pages:
            logger.warning("Pagination: No subcommand pages available")
            return

        # Read current page directly from self
        current_page = self.current_subcommand_page
        # total_pages = len(self.subcommand_pages)

        # Decrement the page counter
        if current_page > 0:
            self.current_subcommand_page = current_page - 1
        else:
            logger.info(f"Pagination: Already at first page ({current_page})")

        # Update the embed with the new page
        if self.current_command:
            if interaction.message:
                embed = await self._create_command_embed(self.current_command)
                view = await self._create_command_view()
                await interaction.message.edit(embed=embed, view=view)
            else:
                logger.warning("Pagination: No message to update")

    # Help command overrides

    async def send_bot_help(self, mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]) -> None:
        """
        Send the main help screen with command categories.

        Parameters
        ----------
        mapping : Mapping[commands.Cog | None, list[commands.Command]]
            Mapping of cogs to their commands.
        """
        await self._get_command_categories(mapping)

        embed = await self._create_main_embed()
        view = await self._create_main_view()

        self.message = await self.get_destination().send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Display help for a specific cog.

        Parameters
        ----------
        cog : commands.Cog
            The cog for which to display help.
        """
        prefix = await self._get_prefix()
        embed = self._embed_base(f"{cog.qualified_name} Commands")

        for command in cog.get_commands():
            self._add_command_field(embed, command, prefix)

            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    self._add_command_field(embed, subcommand, prefix)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, Any, Any]) -> None:
        """
        Display help for a specific command.

        Parameters
        ----------
        command : commands.Command
            The command for which to display help.
        """
        prefix = await self._get_prefix()

        # Format help text with proper quoting for all lines
        help_text = format_multiline_description(command.help)

        embed = self._embed_base(
            title=f"{prefix}{command.qualified_name}",
            description=help_text,
        )

        await self._add_command_help_fields(embed, command)

        if flag_details := self._format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        view = HelpView(self)
        view.add_item(CloseButton())

        await self.get_destination().send(embed=embed, view=view)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """
        Display help for a command group.

        Parameters
        ----------
        group : commands.Group
            The command group for which to display help.
        """
        # For large command groups or JSK, use pagination
        if group.name in {"jsk", "jishaku"} or len(group.commands) > 15:
            # Paginate subcommands
            subcommands = sorted(group.commands, key=lambda x: x.name)
            pages = paginate_items(subcommands, 8)

            # Create direct help view with navigation
            view = DirectHelpView(self, group, pages)
            embed = await view.get_embed()

        else:
            # For smaller groups, add a dropdown to view individual subcommands
            prefix = await self._get_prefix()

            # Format help text with proper quoting for all lines
            help_text = format_multiline_description(group.help)

            embed = self._embed_base(
                title=f"{prefix}{group.qualified_name}",
                description=help_text,
            )
            await self._add_command_help_fields(embed, group)

            # Add all subcommands non-inline
            sorted_cmds = sorted(group.commands, key=lambda x: x.name)
            subcommands_list = "\n".join(f"• `{c.name}` - {c.short_doc or 'No description'}" for c in sorted_cmds)

            embed.add_field(
                name="Subcommands",
                value=f"This command group has the following subcommands:\n\n{subcommands_list}\n\nSelect a subcommand from the dropdown to see more details.",
                inline=False,
            )

            # Create view with dropdown
            view = HelpView(self)

            if subcommand_options := [
                discord.SelectOption(
                    label=cmd.name,
                    value=cmd.name,
                    description=truncate_description(cmd.short_doc or "No description"),
                )
                for cmd in sorted_cmds
            ]:
                subcommand_select = SubcommandSelectMenu(self, subcommand_options, "View detailed subcommand help")
                view.add_item(subcommand_select)

            view.add_item(CloseButton())

            # Create a special handler for this message
            self.current_command = group.name
            self.current_command_obj = group

        await self.get_destination().send(embed=embed, view=view)

    async def send_error_message(self, error: str) -> None:
        """
        Display an error message.

        Parameters
        ----------
        error : str
            The error message to display.
        """
        embed = EmbedCreator.create_embed(
            EmbedCreator.ERROR,
            user_name=self.context.author.name,
            user_display_avatar=self.context.author.display_avatar.url,
            description=error,
        )

        await self.get_destination().send(embed=embed, delete_after=CONST.DEFAULT_DELETE_AFTER)

        # Only log errors that are not related to command not found
        if "no command called" not in error.lower():
            logger.warning(f"An error occurred while sending a help message: {error}")

    def to_reference_list(
        self,
        ctx: commands.Context[commands.Bot],
        commands_list: list[commands.Command[Any, Any, Any]],
        with_groups: bool = True,
    ) -> list[tuple[commands.Command[Any, Any, Any], str | None]]:
        """
        Convert a list of commands to a reference list.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context of the command.
        commands_list : list of commands.Command
            The list of commands to convert.
        with_groups : bool, optional
            Whether to include command groups.

        Returns
        -------
        list of tuple
            A list of tuples, each containing a command and its cog group (or None).
        """
        references: list[tuple[commands.Command[Any, Any, Any], str | None]] = []

        # Helper function to extract cog group from a command
        def get_command_group(cmd: commands.Command[Any, Any, Any]) -> str | None:
            """Extract the command's cog group."""
            if cmd.cog:
                module = getattr(cmd.cog, "__module__", "")
                parts = module.split(".")
                # Assuming the structure is: tux.cogs.<group>...
                if len(parts) >= 3 and parts[1].lower() == "cogs":
                    return parts[2].lower()
            return None

        for cmd in commands_list:
            if isinstance(cmd, commands.Group) and with_groups and cmd.commands:
                child_commands = list(cmd.commands)
                references.append((cmd, get_command_group(cmd)))

                references.extend(
                    (child_cmd, get_command_group(cmd)) for child_cmd in sorted(child_commands, key=lambda x: x.name)
                )
            else:
                references.append((cmd, get_command_group(cmd)))

        return references
