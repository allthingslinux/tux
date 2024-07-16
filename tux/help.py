from collections.abc import Mapping
from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class TuxHelp(commands.HelpCommand):
    def __init__(self):
        self.prefix = CONST.PREFIX
        super().__init__()

    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> None:
        """
        Sends help message for the bot.
        """
        embed = discord.Embed(
            title="Categories",
            color=discord.Color.blurple(),
        )

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

        # TODO: normalize spacing between category and command names

        # Set the description of the embed to the category strings
        embed.description = "\n".join(category_strings.values())

        embed.set_footer(
            text=f"Use {self.prefix}help <category> or {self.prefix}<command> to learn about a category or command.",
        )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Sends help message for a cog.
        """
        embed = discord.Embed(
            title=f"{cog.qualified_name} Commands",
            color=discord.Color.blurple(),
        )

        for command in cog.get_commands():
            embed.add_field(
                name=f"{self.prefix}{command.qualified_name} ({', '.join(command.aliases) if command.aliases else 'No aliases.'})",
                value=f"> {command.short_doc or 'No documentation summary.'}",
                inline=False,
            )

            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    embed.add_field(
                        name=f"{self.prefix}{subcommand.qualified_name} ({', '.join(subcommand.aliases) if subcommand.aliases else 'No aliases.'})",
                        value=f"> {subcommand.short_doc or 'No documentation summary.'}",
                        inline=False,
                    )

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, Any, Any]):
        """
        Sends help message for a command.
        """
        embed = discord.Embed(
            title=f"{self.prefix}{command.qualified_name}",
            description=f"> {command.help or 'No documentation available.'}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Usage", value=f"`{command.signature or 'No usage.'}`", inline=False)
        embed.add_field(
            name="Aliases",
            value=f"`{', '.join(command.aliases)}`" if command.aliases else "No aliases.",
            inline=False,
        )

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]):
        """
        Sends help message for a group.
        """
        embed = discord.Embed(
            title=f"{group.name}",
            description=f"> {group.help or 'No documentation available.'}",
            color=discord.Color.blurple(),
        )

        embed.add_field(name="Usage", value=f"`{group.signature or 'No usage.'}`", inline=False)
        embed.add_field(
            name="Aliases",
            value=f"`{', '.join(group.aliases)}`" if group.aliases else "No aliases.",
            inline=False,
        )

        for command in group.commands:
            embed.add_field(
                name=f"{self.prefix}{command.qualified_name} ({', '.join(command.aliases) if command.aliases else 'No aliases.'})",
                value=f"> {command.short_doc or 'No documentation summary.'}",
                inline=False,
            )

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        logger.error(f"An error occurred while sending help message: {error}")

        embed = EmbedCreator.create_error_embed(
            title="An error occurred while sending help message.",
            description=error,
        )

        await self.get_destination().send(embed=embed)
