"""Help system embed rendering."""

from __future__ import annotations

from typing import Any, get_type_hints

import discord
from discord import SelectOption
from discord.ext import commands

from tux.shared.config import CONFIG
from tux.shared.constants import EMBED_COLORS
from tux.shared.version import get_version

from .utils import format_multiline_description, truncate_description


class HelpRenderer:
    """Handles help embed creation and formatting."""

    def __init__(self, prefix: str) -> None:
        """Initialize the help renderer.

        Parameters
        ----------
        prefix : str
            The command prefix to use in help text formatting.
        """
        self.prefix = prefix

    def create_base_embed(
        self,
        title: str,
        description: str | None = None,
    ) -> discord.Embed:
        """
        Create base embed with consistent styling.

        Returns
        -------
        discord.Embed
            The base embed with title, description, and default color.
        """
        return discord.Embed(
            title=title,
            description=description,
            color=EMBED_COLORS["DEFAULT"],
        )

    def format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        """
        Format flag details for a command.

        Returns
        -------
        str
            Formatted flag details, or empty string if no flags.
        """
        flag_details: list[str] = []

        try:
            type_hints = get_type_hints(command.callback)
        except Exception:
            return ""

        for param_annotation in type_hints.values():
            if not isinstance(param_annotation, type) or not issubclass(
                param_annotation,
                commands.FlagConverter,
            ):
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

        Returns
        -------
        str
            The formatted flag name with appropriate brackets.
        """
        if getattr(flag, "positional", False):
            return f"<{flag.name}>" if flag.required else f"[{flag.name}]"
        return f"-{flag.name}" if flag.required else f"[-{flag.name}]"

    def generate_default_usage(self, command: commands.Command[Any, Any, Any]) -> str:
        """
        Generate default usage string for a command.

        Returns
        -------
        str
            The usage string for the command.
        """
        signature = command.signature.strip()
        if not signature:
            return command.qualified_name

        # Format the signature to look more like Discord's native format
        formatted_signature = signature.replace("[", "<").replace("]", ">")
        return f"{command.qualified_name} {formatted_signature}"

    async def add_command_help_fields(
        self,
        embed: discord.Embed,
        command: commands.Command[Any, Any, Any],
    ) -> None:
        """Add help fields for a command to embed."""
        embed.add_field(
            name="Aliases",
            value=(
                f"`{', '.join(command.aliases)}`" if command.aliases else "No aliases"
            ),
            inline=False,
        )
        usage = command.usage or self.generate_default_usage(command)
        embed.add_field(name="Usage", value=f"`{self.prefix}{usage}`", inline=False)

    def add_command_field(
        self,
        embed: discord.Embed,
        command: commands.Command[Any, Any, Any],
    ) -> None:
        """Add a single command field to embed."""
        command_aliases = (
            ", ".join(command.aliases) if command.aliases else "No aliases"
        )
        embed.add_field(
            name=f"{self.prefix}{command.qualified_name} ({command_aliases})",
            value=f"> {command.short_doc or 'No documentation summary'}",
            inline=False,
        )

    async def create_main_embed(
        self,
        categories: dict[str, dict[str, str]],
    ) -> discord.Embed:
        """
        Create main help embed.

        Returns
        -------
        discord.Embed
            The main help embed with bot information and usage instructions.
        """
        if CONFIG.BOT_INFO.BOT_NAME != "Tux":
            embed = self.create_base_embed(
                "Hello! Welcome to the help command.",
                f"{CONFIG.BOT_INFO.BOT_NAME} is a self-hosted instance of Tux. The bot is written in Python using discord.py.\n\nIf you enjoy using {CONFIG.BOT_INFO.BOT_NAME}, consider contributing to the original project.",
            )
        else:
            embed = self.create_base_embed(
                "Hello! Welcome to the help command.",
                "Tux is an all-in-one bot by the All Things Linux Discord server. The bot is written in Python using discord.py, and we are actively seeking contributors.",
            )

        await self._add_bot_help_fields(embed)
        return embed

    async def _add_bot_help_fields(self, embed: discord.Embed) -> None:
        """Add additional help information about the bot to the embed."""
        embed.add_field(
            name="How to Use",
            value=f"Most commands are hybrid meaning they can be used via prefix `{self.prefix}` OR slash `/`. Commands strictly available via `/` are not listed in the help menu.",
            inline=False,
        )
        embed.add_field(
            name="Command Help",
            value="Select a category from the dropdown, then select a command to view details.",
            inline=False,
        )
        embed.add_field(
            name="Flag Help",
            value=f"Flags in `[]` are optional. Most flags have aliases that can be used.\n> e.g. `{self.prefix}ban @user spamming` or `{self.prefix}b @user spam -silent true`",
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

        bot_name_display = (
            "Tux"
            if CONFIG.BOT_INFO.BOT_NAME == "Tux"
            else f"{CONFIG.BOT_INFO.BOT_NAME} (Tux)"
        )
        owner_info = (
            f"Bot Owner: <@{CONFIG.USER_IDS.BOT_OWNER_ID}>"
            if not CONFIG.BOT_INFO.HIDE_BOT_OWNER and CONFIG.USER_IDS.BOT_OWNER_ID
            else ""
        )

        embed.add_field(
            name="Bot Instance",
            value=f"-# Running {bot_name_display} v `{get_version()}`"
            + (f"\n-# {owner_info}" if owner_info else ""),
            inline=False,
        )

    async def create_category_embed(
        self,
        category: str,
        commands_dict: dict[str, str],
    ) -> discord.Embed:
        """
        Create category-specific embed.

        Returns
        -------
        discord.Embed
            The category embed with command list.
        """
        embed = self.create_base_embed(f"{category.capitalize()} Commands")

        embed.set_footer(text="Select a command from the dropdown to see details.")

        sorted_commands = sorted(commands_dict.items())
        description = "\n".join(
            f"**`{self.prefix}{cmd}`** | {command_list}"
            for cmd, command_list in sorted_commands
        )
        embed.description = description

        return embed

    async def create_command_embed(
        self,
        command: commands.Command[Any, Any, Any],
    ) -> discord.Embed:
        """
        Create command-specific embed.

        Returns
        -------
        discord.Embed
            The command embed with details and usage.
        """
        help_text = format_multiline_description(command.help)
        embed = self.create_base_embed(
            title=f"{self.prefix}{command.qualified_name}",
            description=help_text,
        )

        await self.add_command_help_fields(embed, command)

        # Add flag details if present
        if flag_details := self.format_flag_details(command):
            embed.add_field(
                name="Flags",
                value=f"```\n{flag_details}\n```",
                inline=False,
            )

        # Add subcommands section if this is a group
        if isinstance(command, commands.Group) and command.commands:
            sorted_cmds = sorted(command.commands, key=lambda x: x.name)

            # Skip subcommands field for large command groups like jishaku that use pagination
            is_large_group = command.name in {"jsk", "jishaku"} or len(sorted_cmds) > 15
            if not is_large_group:
                if nested_groups := [
                    cmd
                    for cmd in sorted_cmds
                    if isinstance(cmd, commands.Group) and cmd.commands
                ]:
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

                subcommands_list = "\n".join(
                    f"• `{c.name}`{' ≡' if isinstance(c, commands.Group) and c.commands else ''} - {c.short_doc or 'No description'}"
                    for c in sorted_cmds
                )
                embed.add_field(
                    name="Subcommands",
                    value=(
                        f"This command group has the following subcommands:\n\n{subcommands_list}\n\nSelect a subcommand from the dropdown to see more details."
                    ),
                    inline=False,
                )
            else:
                # For large groups, just mention the count and let the select menu handle navigation
                embed.add_field(
                    name="Subcommands",
                    value=f"This command group has {len(sorted_cmds)} subcommands.\n\nUse the dropdown below to select a subcommand.",
                    inline=False,
                )

        return embed

    async def create_subcommand_embed(
        self,
        parent_name: str,
        subcommand: commands.Command[Any, Any, Any],
    ) -> discord.Embed:
        """
        Create subcommand-specific embed.

        Returns
        -------
        discord.Embed
            The subcommand embed with details and usage.
        """
        help_text = format_multiline_description(subcommand.help)

        embed = self.create_base_embed(
            title=f"{self.prefix}{subcommand.qualified_name}",
            description=help_text,
        )

        await self.add_command_help_fields(embed, subcommand)

        if flag_details := self.format_flag_details(subcommand):
            embed.add_field(
                name="Flags",
                value=f"```\n{flag_details}\n```",
                inline=False,
            )

        return embed

    def create_category_options(
        self,
        categories: dict[str, dict[str, str]],
    ) -> list[discord.SelectOption]:
        """
        Create select options for categories.

        Returns
        -------
        list[discord.SelectOption]
            List of select options for each category.
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
            "extra": "❓",
            "config": "⚙️",
            "features": "✨",
        }

        options: list[discord.SelectOption] = []
        for category, commands_dict in categories.items():
            if any(commands_dict.values()):
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

    def create_command_options(
        self,
        commands_dict: dict[str, str],
        command_mapping: dict[str, commands.Command[Any, Any, Any]],
    ) -> list[discord.SelectOption]:
        """
        Create select options for commands.

        Returns
        -------
        list[discord.SelectOption]
            List of select options for each command, sorted by label.
        """
        options: list[discord.SelectOption] = []

        for cmd_name in commands_dict:
            command = command_mapping.get(cmd_name)
            description = command.short_doc if command else "No description"
            truncated_desc = truncate_description(description)
            options.append(
                SelectOption(
                    label=cmd_name,
                    value=cmd_name,
                    description=truncated_desc,
                ),
            )

        return sorted(options, key=lambda o: o.label)

    def create_subcommand_options(
        self,
        subcommands: list[commands.Command[Any, Any, Any]],
    ) -> list[SelectOption]:
        """
        Create select options for subcommands.

        Returns
        -------
        list[SelectOption]
            List of select options for each subcommand.
        """
        # Special handling for jishaku to prevent loading all subcommands
        if (
            not subcommands
            or not subcommands[0].parent
            or not hasattr(subcommands[0].parent, "name")
            or getattr(subcommands[0].parent, "name", None) not in {"jsk", "jishaku"}
        ):
            # Normal handling for other command groups
            return [
                SelectOption(
                    label=subcmd.name,
                    value=subcmd.name,
                    description=truncate_description(
                        subcmd.short_doc or "No description",
                    ),
                )
                for subcmd in sorted(subcommands, key=lambda x: x.name)
            ]

        # Only include a few important jishaku commands
        essential_subcmds = ["py", "shell", "cat", "curl", "pip", "git", "help"]

        subcommand_options: list[SelectOption] = []
        for subcmd_name in essential_subcmds:
            if subcmd := discord.utils.get(subcommands, name=subcmd_name):
                description = truncate_description(subcmd.short_doc or "No description")
                subcommand_options.append(
                    SelectOption(
                        label=subcmd.name,
                        value=subcmd.name,
                        description=description,
                    ),
                )

        # Add an option to suggest using jsk help
        subcommand_options.append(
            SelectOption(
                label="See all commands",
                value="_see_all",
                description="Use jsk help command for complete list",
            ),
        )

        return subcommand_options
