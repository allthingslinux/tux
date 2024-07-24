from collections.abc import Mapping
from typing import Any, get_type_hints

import discord
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class TuxHelp(commands.HelpCommand):
    def __init__(self):
        self.prefix = CONST.PREFIX
        super().__init__(
            command_attrs={
                "help": "Lists all categories and commands.",
                "aliases": ["h"],
                "usage": "$help <category> or <command>",
            },
        )

    def embed_base(self, title: str, description: str | None = None) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            color=CONST.EMBED_COLORS["DEFAULT"],
        )

    def add_command_field(self, embed: discord.Embed, command: commands.Command[Any, Any, Any], prefix: str):
        embed.add_field(
            name=f"{prefix}{command.qualified_name} ({', '.join(command.aliases) if command.aliases else 'No aliases.'})",
            value=f"> {command.short_doc or 'No documentation summary.'}",
            inline=False,
        )

    def format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        try:
            type_hints = get_type_hints(command.callback)
        except Exception:
            type_hints = {}

        flag_details: list[str] = []

        for param_annotation in type_hints.values():
            if isinstance(param_annotation, type) and issubclass(param_annotation, commands.FlagConverter):
                command_flags = param_annotation.__commands_flags__
                for flag in command_flags.values():
                    flag_type = flag.annotation if flag.annotation is not None else "Any"
                    if isinstance(flag_type, type):
                        flag_type = flag_type.__name__
                    flag_name_format = f"--[{flag.name}]" if flag.required else f"--<{flag.name}>"
                    flag_str = f"{flag_name_format}"
                    if flag.aliases:
                        flag_str += f" ({', '.join(flag.aliases)})"
                    flag_str += f"\n\t{flag.description or 'No description provided.'}"
                    flag_str += f"\n\tType: `{flag_type}`"
                    if flag.default is not discord.utils.MISSING:
                        flag_str += f"\n\tDefault: {flag.default}"
                    flag_str += "\n\n"
                    flag_details.append(flag_str)
        return "".join(flag_details)

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> None:
        """
        Sends help message for the bot.
        """
        embed = self.embed_base("Categories")

        category_strings: dict[str, str] = {}

        for cog, mapping_commands in mapping.items():
            for command in mapping_commands:
                if cog is None:
                    continue

                # Get the category and command name
                category = cog.qualified_name
                command_name = command.name

                # Check if the category is already in the list
                if category not in category_strings:
                    category_strings[category] = f"**{category}** | "

                # Add the command name to the list of commands for the category
                category_strings[category] += f"`{command_name}` "

                # Check if the command is a group command and add subcommands
                if isinstance(command, commands.Group):
                    for subcommand in command.commands:
                        category_strings[category] += f"`{subcommand.name}` "

        embed.description = "\n".join(category_strings.values())

        embed.set_footer(text=f"Use {self.prefix}help [category] or [command] to learn about it.")

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Sends help message for a cog.
        """
        embed = self.embed_base(f"{cog.qualified_name} Commands")

        for command in cog.get_commands():
            self.add_command_field(embed, command, self.prefix)

            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    self.add_command_field(embed, subcommand, self.prefix)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, Any, Any]):
        """
        Sends help message for a command.
        """
        embed = self.embed_base(
            title=f"{self.prefix}{command.qualified_name}",
            description=f"> {command.help or 'No documentation available.'}",
        )

        embed.add_field(name="Usage", value=f"`{command.signature or 'No usage.'}`", inline=False)
        embed.add_field(
            name="Aliases",
            value=f"`{', '.join(command.aliases)}`" if command.aliases else "No aliases.",
            inline=False,
        )

        if flag_details := self.format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]):
        """
        Sends help message for a group.
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
        logger.error(f"An error occurred while sending a help message: {error}")

        embed = EmbedCreator.create_error_embed(
            title="An error occurred while sending help message.",
            description=error,
        )

        await self.get_destination().send(embed=embed)
