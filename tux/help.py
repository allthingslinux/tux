import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, get_type_hints

import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu
from reactionmenu.abc import Page
from reactionmenu.views_menu import ViewSelect

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class TuxHelp(commands.HelpCommand):
    def __init__(self):
        """Initializes the TuxHelp command with necessary attributes."""
        super().__init__(
            command_attrs={
                "help": "Lists all commands and sub-commands.",
                "aliases": ["h"],
                "usage": "$help <command> or <sub-command>",
            },
        )

    async def _get_prefix(self) -> str:
        """
        Dynamically fetches the prefix from the context or uses a default prefix constant.

        Returns
        -------
        str
            The prefix used to invoke the bot.
        """

        return self.context.clean_prefix or CONST.DEFAULT_PREFIX

    def _embed_base(self, title: str, description: str | None = None) -> discord.Embed:
        """
        Creates a base embed with uniform styling.

        Parameters
        ----------
        title : str
            The title of the embed.
        description : str | None
            The description of the embed.

        Returns
        -------
        discord.Embed
            The created embed.
        """

        return discord.Embed(
            title=title,
            description=description,
            color=CONST.EMBED_COLORS["DEFAULT"],
        )

    def _add_command_field(
        self,
        embed: discord.Embed,
        command: commands.Command[Any, Any, Any],
        prefix: str,
    ) -> None:
        """
        Adds a command's details as a field to an embed.

        Parameters
        ----------
        embed : discord.Embed
            The embed to which the command details will be added.
        command : commands.Command[Any, Any, Any]
            The command whose details are to be added.
        prefix : str
            The prefix used to invoke the command.
        """

        command_aliases = ", ".join(command.aliases) if command.aliases else "No aliases."

        embed.add_field(
            name=f"{prefix}{command.qualified_name} ({command_aliases})",
            value=f"> {command.short_doc or 'No documentation summary.'}",
            inline=False,
        )

    def _get_flag_type(self, flag_annotation: Any) -> str:
        """
        Determines the type of a flag based on its annotation.

        Parameters
        ----------
        flag_annotation : Any
            The annotation of the flag.

        Returns
        -------
        str
            The type of the flag.
        """

        match flag_annotation:
            case None:
                return "Any"
            case t if isinstance(t, type):
                return t.__name__
            case _:
                return str(flag_annotation)

    def _format_flag_name(self, flag: commands.Flag) -> str:
        """
        Formats the flag name based on whether it is required.

        Parameters
        ----------
        flag : commands.Flag
            The flag to be formatted.

        Returns
        -------
        str
            The formatted flag name.
        """

        return f"-[{flag.name}]" if flag.required else f"-<{flag.name}>"

    def _format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        """
        Formats the details of flags for a command.

        Parameters
        ----------
        command : commands.Command[Any, Any, Any]
            The command whose flag details are to be formatted.

        Returns
        -------
        str
            The formatted flag details.
        """
        flag_details: list[str] = []

        try:
            type_hints = get_type_hints(command.callback)
        except Exception:
            type_hints = {}

        for param_annotation in type_hints.values():
            if not isinstance(param_annotation, type) or not issubclass(param_annotation, commands.FlagConverter):
                continue

            for flag in param_annotation.__commands_flags__.values():
                # flag_type = self._get_flag_type(flag.annotation)
                flag_str = self._format_flag_name(flag)

                if flag.aliases:
                    flag_str += f" ({', '.join(flag.aliases)})"
                # else:
                # flag_str += f" : {flag_type}"

                flag_str += f"\n\t{flag.description or 'No description provided.'}"

                if flag.default is not discord.utils.MISSING:
                    flag_str += f"\n\tDefault: {flag.default}"

                flag_details.append(flag_str)

        return "\n\n".join(flag_details)

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> None:
        """
        Sends help messages for the bot with pagination based on the folder it is in.

        Parameters
        ----------
        mapping : Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]
            The mapping of cogs to commands.
        """

        menu = ViewMenu(
            self.context,
            menu_type=ViewMenu.TypeEmbed,
            delete_on_timeout=True,
            timeout=180,
            show_page_director=False,
        )

        embed = self._embed_base(
            "Hello! Welcome to the help command.",
            "Tux is an all-in-one bot for the All Things Linux Discord server. The bot is written in Python 3.12 using discord.py, and we are actively seeking contributors!",
        )

        await self._add_bot_help_fields(embed)
        menu.add_page(embed)
        await self._add_cog_pages(menu, mapping)

        await menu.start()

    async def _add_bot_help_fields(self, embed: discord.Embed) -> None:
        """
        Adds additional help information about the bot.

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
            value=f"Use `{prefix}help <command>` or `{prefix}help <subcommand>` to learn about a specific command.\n> e.g. `{prefix}help ban` or `{prefix}h dev load_cog`",
            inline=False,
        )
        embed.add_field(
            name="Flag Help",
            value=f"Flags in `[]` are required and `<>` are optional. Most flags have aliases that can be used.\n> e.g. `{prefix}ban @user -reason spamming` or `{prefix}b @user -r spamming`",
            inline=False,
        )
        embed.add_field(
            name="Support Server",
            value="[Need support? Join Server](https://discord.gg/gpmSjcjQxg)",
            inline=True,
        )
        embed.add_field(
            name="GitHub Repository",
            value="[Help contribute! View Repo](https://github.com/allthingslinux/tux)",
            inline=True,
        )

    async def _add_cog_pages(
        self,
        menu: ViewMenu,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> None:
        """
        Adds pages for each cog category to the help menu.

        Parameters
        ----------
        menu : ViewMenu
            The menu to which the pages will be added.
        mapping : Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]
            The mapping of cogs to commands.
        """

        command_categories = await self._get_command_categories(mapping)
        cog_groups = self._get_cog_groups()
        select_options = await self._create_select_options(command_categories, cog_groups, menu)
        self._add_navigation_and_selection(menu, select_options)

    async def _get_command_categories(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> dict[str, dict[str, str]]:
        """
        Retrieves the command categories and their corresponding commands.

        Parameters
        ----------
        mapping : Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]
            The mapping of cogs to commands.

        Returns
        -------
        dict[str, dict[str, str]]
            The dictionary of command categories and commands.
        """

        command_categories: dict[str, dict[str, str]] = {}

        for cog, mapping_commands in mapping.items():
            if cog and len(mapping_commands) > 0:
                cog_group = self._extract_cog_group(cog) or "extra"
                command_categories.setdefault(cog_group, {})
                for command in mapping_commands:
                    cmd_name_and_aliases = f"`{command.name}`"
                    if command.aliases:
                        cmd_name_and_aliases += f" ({', '.join(f'`{alias}`' for alias in command.aliases)})"
                    command_categories[cog_group][command.name] = cmd_name_and_aliases

        return command_categories

    def _get_cog_groups(self) -> list[str]:
        """
        Retrieves a list of cog groups from the 'cogs' folder.

        Returns
        -------
        list[str]
            A list of cog groups.
        """

        return [d for d in os.listdir("./tux/cogs") if Path(f"./tux/cogs/{d}").is_dir() and d != "__pycache__"]

    async def _create_select_options(
        self,
        command_categories: dict[str, dict[str, str]],
        cog_groups: list[str],
        menu: ViewMenu,
    ) -> dict[discord.SelectOption, list[Page]]:
        """
        Creates select options for each command category.

        Parameters
        ----------
        command_categories : dict[str, dict[str, str]]
            The dictionary of command categories.
        cog_groups : list[str]
            The list of cog groups.
        menu : ViewMenu
            The menu to which the select options will be added.

        Returns
        -------
        dict[discord.SelectOption, list[Page]]
            The created select options.
        """

        select_options: dict[discord.SelectOption, list[Page]] = {}

        for index, cog_group in enumerate(cog_groups, start=1):
            if cog_group in command_categories and any(command_categories[cog_group].values()):
                embed = self._embed_base(f"{cog_group.capitalize()} Commands", "\n")
                embed.set_footer(
                    text=f"Use {await self._get_prefix()}help <command> or <subcommand> to learn about it.",
                )

                for cmd, command_list in command_categories[cog_group].items():
                    embed.add_field(name=cmd, value=command_list, inline=False)

                page = Page(embed=embed)
                menu.add_page(embed)

                select_options[discord.SelectOption(label=cog_group.capitalize(), emoji=f"{index}️⃣")] = [page]

        return select_options

    def _add_navigation_and_selection(
        self,
        menu: ViewMenu,
        select_options: dict[discord.SelectOption, list[Page]],
    ) -> None:
        """
        Adds navigation buttons and select options to the help menu.

        Parameters
        ----------
        menu : ViewMenu
            The menu to which the navigation and selection will be added.
        select_options : dict[discord.SelectOption, list[Page]]
            The dictionary of select options.
        """

        menu.add_select(ViewSelect(title="Command Categories", options=select_options))
        menu.add_button(ViewButton.end_session())

    def _extract_cog_group(self, cog: commands.Cog) -> str | None:
        """
        Extracts the cog group from a cog's string representation.

        Parameters
        ----------
        cog : commands.Cog
            The cog from which the group is to be extracted.

        Returns
        -------
        str | None
            The extracted cog group or None if not found.
        """

        if match := re.search(r"<cogs\.([^\.]+)\..*>", str(cog)):
            return match[1]
        return None

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Sends a help message for a specific cog.

        Parameters
        ----------
        cog : commands.Cog
            The cog for which the help message is to be sent.
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
        Sends a help message for a specific command.

        Parameters
        ----------
        command : commands.Command[Any, Any, Any]
            The command for which the help message is to be sent.
        """

        prefix = await self._get_prefix()

        embed = self._embed_base(
            title=f"{prefix}{command.qualified_name}",
            description=f"> {command.help or 'No documentation available.'}",
        )

        await self._add_command_help_fields(embed, command)

        if flag_details := self._format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        await self.get_destination().send(embed=embed)

    async def _add_command_help_fields(self, embed: discord.Embed, command: commands.Command[Any, Any, Any]) -> None:
        """
        Adds fields with usage and alias information for a command to an embed.

        Parameters
        ----------
        embed : discord.Embed
            The embed to which the fields will be added.
        command : commands.Command[Any, Any, Any]
            The command whose details are to be added.
        """

        prefix = await self._get_prefix()

        embed.add_field(
            name="Usage",
            value=f"`{prefix}{command.usage or 'No usage.'}`",
            inline=False,
        )
        embed.add_field(
            name="Aliases",
            value=(f"`{', '.join(command.aliases)}`" if command.aliases else "No aliases."),
            inline=False,
        )

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """
        Sends a help message for a specific command group.

        Parameters
        ----------
        group : commands.Group[Any, Any, Any]
            The group for which the help message is to be sent.
        """

        prefix = await self._get_prefix()

        embed = self._embed_base(f"{group.name}", f"> {group.help or 'No documentation available.'}")

        await self._add_command_help_fields(embed, group)
        for command in group.commands:
            self._add_command_field(embed, command, prefix)

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        """
        Sends an error message.

        Parameters
        ----------
        error : str
            The error message to be sent.
        """

        logger.error(f"An error occurred while sending a help message: {error}")

        embed = EmbedCreator.create_error_embed(
            title="An error occurred while sending help message.",
            description=error,
        )

        await self.get_destination().send(embed=embed, delete_after=30)
