"""Help system embed rendering."""

from __future__ import annotations

from typing import Any, get_type_hints

import discord
from discord import SelectOption
from discord.ext import commands

from .utils import format_multiline_description, truncate_description


class HelpRenderer:
    """Handles help embed creation and formatting."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def create_base_embed(self, title: str, description: str | None = None) -> discord.Embed:
        """Create base embed with consistent styling."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Use {self.prefix}help <command> for more info on a command.")
        return embed

    def format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        """Format flag details for a command."""
        if not hasattr(command, "clean_params"):
            return ""

        flag_details: list[str] = []
        for param_name in command.clean_params:
            if param_name == "flags":
                param_annotation = get_type_hints(command.callback).get("flags")
                if param_annotation and issubclass(param_annotation, commands.FlagConverter):
                    flags = param_annotation.get_flags()
                    flag_details.extend(
                        f"--{flag_name}: {flag.description or 'No description'}" for flag_name, flag in flags.items()
                    )

        return "\n".join(flag_details)

    def generate_default_usage(self, command: commands.Command[Any, Any, Any]) -> str:
        """Generate default usage string for a command."""
        usage_parts = [f"{self.prefix}{command.qualified_name}"]

        if hasattr(command, "clean_params"):
            for param_name, param in command.clean_params.items():
                if param_name not in ("self", "ctx"):
                    if param.default == param.empty:
                        usage_parts.append(f"<{param_name}>")
                    else:
                        usage_parts.append(f"[{param_name}]")

        return " ".join(usage_parts)

    async def add_command_help_fields(self, embed: discord.Embed, command: commands.Command[Any, Any, Any]) -> None:
        """Add help fields for a command to embed."""
        if command.usage:
            embed.add_field(name="Usage", value=f"`{self.prefix}{command.usage}`", inline=False)
        else:
            usage = self.generate_default_usage(command)
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        if command.aliases:
            aliases = ", ".join(f"`{alias}`" for alias in command.aliases)
            embed.add_field(name="Aliases", value=aliases, inline=True)

        if flag_details := self.format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

    def add_command_field(self, embed: discord.Embed, command: commands.Command[Any, Any, Any]) -> None:
        """Add a single command field to embed."""
        description = truncate_description(command.help or "No description available.", 100)
        embed.add_field(
            name=f"{self.prefix}{command.qualified_name}",
            value=description,
            inline=True,
        )

    async def create_main_embed(self, categories: dict[str, dict[str, str]]) -> discord.Embed:
        """Create main help embed."""
        embed = self.create_base_embed(
            title="📚 Tux Help Menu",
            description="Select a category below to view available commands.",
        )

        for category_name, commands_dict in categories.items():
            command_count = len(commands_dict)
            embed.add_field(
                name=f"📂 {category_name}",
                value=f"{command_count} command{'s' if command_count != 1 else ''}",
                inline=True,
            )

        return embed

    async def create_category_embed(self, category: str, commands_dict: dict[str, str]) -> discord.Embed:
        """Create category-specific embed."""
        embed = self.create_base_embed(
            title=f"📂 {category} Commands",
            description=f"Commands available in the {category} category.",
        )

        for command_name, description in commands_dict.items():
            embed.add_field(
                name=f"{self.prefix}{command_name}",
                value=truncate_description(description, 100),
                inline=True,
            )

        return embed

    async def create_command_embed(self, command: commands.Command[Any, Any, Any]) -> discord.Embed:
        """Create command-specific embed."""
        description = format_multiline_description(command.help or "No description available.")

        embed = self.create_base_embed(
            title=f"🔧 {command.qualified_name}",
            description=description,
        )

        await self.add_command_help_fields(embed, command)
        return embed

    async def create_subcommand_embed(
        self,
        parent_name: str,
        subcommand: commands.Command[Any, Any, Any],
    ) -> discord.Embed:
        """Create subcommand-specific embed."""
        description = format_multiline_description(subcommand.help or "No description available.")

        embed = self.create_base_embed(
            title=f"🔧 {parent_name} {subcommand.name}",
            description=description,
        )

        await self.add_command_help_fields(embed, subcommand)
        return embed

    def create_category_options(self, categories: dict[str, dict[str, str]]) -> list[discord.SelectOption]:
        """Create select options for categories."""
        return [
            discord.SelectOption(
                label=category_name,
                description=f"{len(commands_dict)} commands available",
                value=category_name,
            )
            for category_name, commands_dict in categories.items()
        ]

    def create_command_options(self, commands_dict: dict[str, str]) -> list[discord.SelectOption]:
        """Create select options for commands."""
        return [
            discord.SelectOption(
                label=command_name,
                description=truncate_description(description, 100),
                value=command_name,
            )
            for command_name, description in commands_dict.items()
        ]

    def create_subcommand_options(self, subcommands: list[commands.Command[Any, Any, Any]]) -> list[SelectOption]:
        """Create select options for subcommands."""
        return [
            SelectOption(
                label=subcommand.name,
                description=truncate_description(subcommand.help or "No description", 100),
                value=subcommand.name,
            )
            for subcommand in subcommands
        ]
