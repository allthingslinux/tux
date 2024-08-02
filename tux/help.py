import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, get_type_hints

import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu
from reactionmenu.views_menu import ViewSelect

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class TuxHelp(commands.HelpCommand):
    def __init__(self):
        self.prefix = CONST.PREFIX
        super().__init__(
            command_attrs={
                "help": "Lists all commands and sub-commands.",
                "aliases": ["h"],
                "usage": "$help <command> or <sub-command>",
            },
        )

    def embed_base(self, title: str, description: str | None = None) -> discord.Embed:
        """
        Creates a base embed for help messages.

        Parameters
        ----------
        title : str
            The title of the embed.
        description : str | None
            The description of the embed.

        Returns
        -------
        discord.Embed
            The base embed for help messages.
        """

        return discord.Embed(
            title=title,
            description=description,
            color=CONST.EMBED_COLORS["DEFAULT"],
        )

    def add_command_field(
        self,
        embed: discord.Embed,
        command: commands.Command[Any, Any, Any],
        prefix: str,
    ) -> None:
        """
        Adds a command field to an embed.

        Parameters
        ----------
        embed : discord.Embed
            The embed to add the command field to.
        command : commands.Command[Any, Any, Any]
            The command to add to the embed.
        prefix : str
            The prefix to use for the command.
        """

        embed.add_field(
            name=f"{prefix}{command.qualified_name} ({', '.join(command.aliases) if command.aliases else 'No aliases.'})",
            value=f"> {command.short_doc or 'No documentation summary.'}",
            inline=False,
        )

    def _get_flag_type(self, flag_annotation: Any) -> Any:
        """
        Gets the flag type for a command.

        Parameters
        ----------
        flag_annotation : Any
            The flag annotation to get the type for.

        Returns
        -------
        Any
            The flag type.
        """

        if flag_annotation is None:
            return "Any"
        if isinstance(flag_annotation, type):
            return flag_annotation.__name__
        return flag_annotation

    def format_flag_name(self, flag: commands.Flag) -> str:
        """
        Formats the flag name for a command.

        Parameters
        ----------
        flag : commands.Flag
            The flag to format the name for.

        Returns
        -------
        str
            The formatted flag name.
        """

        return f"--[{flag.name}]" if flag.required else f"--<{flag.name}>"

    def format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        """
        Formats the flag details for a command.

        Parameters
        ----------
        command : commands.Command[Any, Any, Any]
            The command to format the flag details for.

        Returns
        -------
        str
            The formatted flag details.
        """

        try:
            type_hints = get_type_hints(command.callback)
        except Exception:
            type_hints = {}

        flag_details: list[str] = []

        # Iterate over the type hints and get the flag details
        for param_annotation in type_hints.values():
            # Check if the parameter annotation is a FlagConverter
            if not isinstance(param_annotation, type) or not issubclass(param_annotation, commands.FlagConverter):
                continue

            # Get the flags from the parameter annotation
            command_flags = param_annotation.__commands_flags__

            # Iterate over the flags and get the flag details
            for flag in command_flags.values():
                flag_type = self._get_flag_type(flag.annotation)
                flag_str = self.format_flag_name(flag)

                # Add the flag aliases if they exist
                if flag.aliases:
                    alias_list = ", ".join(flag.aliases)
                    flag_str += f" ({alias_list})"

                # Add the flag description if it exists
                flag_str += f"\n\t{flag.description or 'No description provided.'}"

                # Add the flag type if it exists e.g. int, str, etc.
                flag_str += f"\n\tType: `{flag_type}`"

                # Add the default value if it exists e.g. 5, True, etc.
                if flag.default is not discord.utils.MISSING:
                    flag_str += f"\n\tDefault: {flag.default}"

                flag_details.append(flag_str)

        return "\n\n".join(flag_details)

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> None:
        """
        Sends help message for the bot with pagination based on the folder it is in.

        Parameters
        ----------
        mapping : Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]
            The mapping of cogs to commands.
        """
        
        # Make the first info page of the command
        menu = ViewMenu(self.context, menu_type=ViewMenu.TypeEmbed)
        embed = self.embed_base("Header Text")
        embed.set_footer(text=f"Use {self.prefix}help <command> or <sub-command> to learn about it.")
        menu.add_page(embed)
        
        command_categories: dict[str, dict[str, str]] = {}
        # Iterate over the mapping and build the command categories
        for cog, mapping_commands in mapping.items():
            if cog is None:
                continue

            # Check if the cog is in the cogs folder
            if match := re.search(r"<cogs\.([^\.]+)\..*>", str(cog)):
                cog_group: str = match[1]
            else:
                cog_group = "extra"

            if len(mapping_commands) == 0:
                continue

            cmd = cog.qualified_name

            # Check if the cog group is in the command categories
            if cog_group not in command_categories:
                command_categories[cog_group] = {}

            # Check if the command is in the command categories for the cog group
            if cmd not in command_categories[cog_group]:
                command_categories[cog_group][cmd] = ""

            # For each subcommand in the command, add it to the command categories for the cog group and command
            for subcmd in mapping_commands:
                command_name = subcmd.name
                command_categories[cog_group][cmd] += f"`{command_name}` "

                # Check if the subcommand is a group and add the subcommands to the command categories for the cog group and command
                if isinstance(subcmd, commands.Group):
                    command_categories[cog_group][cmd] += "".join(f"`{subcmd.name}` " for subcmd in subcmd.commands)

        # Get the cog groups from the cogs folder
        cog_groups = [d for d in os.listdir("./tux/cogs") if Path(f"./tux/cogs/{d}").is_dir() and d != "__pycache__"]

        # Iterate over the cog groups and add the commands to the menu
        for cog_group_ in cog_groups:
            if cog_group_ in command_categories and any(
                command_categories[cog_group_].values(),
            ):  # Create the base of the embed with a header and footer
                header = f"{cog_group_.capitalize()} Commands"
                embed = self.embed_base(header, "\n")
                embed.set_footer(text=f"Use {self.prefix}help <command> or <sub-command> to learn about it.")

                # Iterate over the commands in the cog group and add them to the embed
                for cmd, command_list in command_categories[cog_group_].items():
                    embed.add_field(name=cmd, value=command_list, inline=False)

                menu.add_page(embed)
                
        pagenumbers_dict: dict[int, str] = {1: "One", 2: "Two"}

        menu.add_button(ViewButton.back())
        menu.add_go_to_select(ViewSelect.GoTo(title="Go to page...", page_numbers=pagenumbers_dict))
        menu.add_button(ViewButton.next())
        menu.add_button(ViewButton.end_session())

        await menu.start()


    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Sends help message for a cog.

        Parameters
        ----------
        cog : commands.Cog
            The cog to send the help message for.
        """

        embed = self.embed_base(f"{cog.qualified_name} Commands")

        # For each command in the cog, add it to the embed
        for command in cog.get_commands():
            self.add_command_field(embed, command, self.prefix)

            # Check if the command is a group and add the subcommands to the embed
            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    self.add_command_field(embed, subcommand, self.prefix)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, Any, Any]) -> None:
        """
        Sends help message for a command.

        Parameters
        ----------
        command : commands.Command[Any, Any, Any]
            The command to send the help message for.
        """

        embed = self.embed_base(
            title=f"{self.prefix}{command.qualified_name}",
            description=f"> {command.help or 'No documentation available.'}",
        )

        embed.add_field(name="Usage", value=f"`{command.signature or 'No usage.'}`", inline=False)
        embed.add_field(
            name="Aliases",
            value=(f"`{', '.join(command.aliases)}`" if command.aliases else "No aliases."),
            inline=False,
        )

        if flag_details := self.format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """
        Sends help message for a group.

        Parameters
        ----------
        group : commands.Group[Any, Any, Any]
            The group to send the help message for.
        """

        embed = self.embed_base(f"{group.name}", f"> {group.help or 'No documentation available.'}")

        embed.add_field(name="Usage", value=f"`{group.signature or 'No usage.'}`", inline=False)

        embed.add_field(
            name="Aliases",
            value=f"`{', '.join(group.aliases)}`" if group.aliases else "No aliases.",
            inline=False,
        )

        for command in group.commands:
            self.add_command_field(embed, command, self.prefix)

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        """
        Sends an error message.

        Parameters
        ----------
        error : str
            The error message to send.
        """

        logger.error(f"An error occurred while sending a help message: {error}")

        embed = EmbedCreator.create_error_embed(
            title="An error occurred while sending help message.",
            description=error,
        )

        await self.get_destination().send(embed=embed, delete_after=30)
