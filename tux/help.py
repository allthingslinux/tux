from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

import discord
from discord.ext import commands
from loguru import logger

from tux.ui.embeds import EmbedCreator
from tux.utils.config import CONFIG
from tux.utils.constants import CONST
from tux.utils.env import get_current_env


class HelpSelectMenu(discord.ui.Select[discord.ui.View]):
    def __init__(self, help_command: "TuxHelp", options: list[discord.SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )
        self.help_command = help_command

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        value = self.values[0]
        await self.help_command.on_category_select(interaction, value)


class CommandSelectMenu(discord.ui.Select[discord.ui.View]):
    def __init__(self, help_command: "TuxHelp", options: list[discord.SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )
        self.help_command = help_command

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        value = self.values[0]
        await self.help_command.on_command_select(interaction, value)


class BackButton(discord.ui.Button[discord.ui.View]):
    def __init__(self, help_command: "TuxHelp"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Back",
            emoji="↩️",
            custom_id="back_button",
        )
        self.help_command = help_command

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.help_command.on_back_button(interaction)


class CloseButton(discord.ui.Button[discord.ui.View]):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Close",
            emoji="✖️",
            custom_id="close_button",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.message:
            await interaction.message.delete()


class HelpView(discord.ui.View):
    def __init__(self, help_command: "TuxHelp", timeout: int = 180):
        super().__init__(timeout=timeout)
        self.help_command = help_command


CommandT = TypeVar("CommandT", bound=commands.Command[Any, Any, Any])


class TuxHelp(commands.HelpCommand):
    def __init__(self):
        """Initializes the TuxHelp command with necessary attributes."""
        super().__init__(
            command_attrs={
                "help": "Lists all commands and sub-commands.",
                "aliases": ["h", "commands"],
                "usage": "$help <command> or <sub-command>",
            },
        )
        self._prefix_cache: dict[int | None, str] = {}
        self._category_cache: dict[str, dict[str, str]] = {}
        self.current_category: str | None = None
        self.current_page: str = "main"
        self.message: discord.Message | None = None
        self.command_mapping: dict[str, dict[str, commands.Command[Any, Any, Any]]] | None = None

    async def _get_prefix(self) -> str:
        """Fetches and caches the prefix for each guild."""
        guild_id = self.context.guild.id if self.context.guild else None

        if guild_id not in self._prefix_cache:
            # Fetch and cache the prefix specific to the guild
            self._prefix_cache[guild_id] = self.context.clean_prefix or CONFIG.DEFAULT_PREFIX

        return self._prefix_cache[guild_id]

    def _embed_base(self, title: str, description: str | None = None) -> discord.Embed:
        """Creates a base embed with uniform styling."""
        return discord.Embed(
            title=title,
            description=description,
            color=CONST.EMBED_COLORS["DEFAULT"],
        )

    # Flag Formatting
    def _format_flag_details(self, command: commands.Command[Any, Any, Any]) -> str:
        """Formats the details of flags for a command."""
        flag_details: list[str] = []

        try:
            type_hints = get_type_hints(command.callback)
        except Exception:
            type_hints = {}

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
        """Formats the flag name based on whether it is required and positional."""
        if getattr(flag, "positional", False):
            return f"<{flag.name}>" if flag.required else f"[{flag.name}]"
        return f"-{flag.name}" if flag.required else f"[-{flag.name}]"

    # Command Fields and Mapping
    def _generate_default_usage(self, command: commands.Command[Any, Any, Any]) -> str:
        """Generates a default usage string based on command parameters when custom usage is missing."""
        signature = command.signature.strip()
        if not signature:
            return command.qualified_name

        # Format the signature to look more like Discord's native format
        # Replace things like [optional] with <optional>
        formatted_signature = signature.replace("[", "<").replace("]", ">")
        return f"{command.qualified_name} {formatted_signature}"

    async def _add_command_help_fields(self, embed: discord.Embed, command: commands.Command[Any, Any, Any]) -> None:
        """Adds fields with usage and alias information for a command to an embed."""
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
        """Adds a command's details as a field to an embed."""
        command_aliases = ", ".join(command.aliases) if command.aliases else "No aliases"
        embed.add_field(
            name=f"{prefix}{command.qualified_name} ({command_aliases})",
            value=f"> {command.short_doc or 'No documentation summary'}",
            inline=False,
        )

    async def _create_category_options(self) -> list[discord.SelectOption]:
        """Creates select options for the category select menu."""
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
        """Creates select options for commands in the selected category."""
        options: list[discord.SelectOption] = []

        if self.command_mapping and category in self.command_mapping:
            for cmd_name, cmd in self.command_mapping[category].items():
                description = cmd.short_doc or "No description"
                # Truncate description if too long
                if len(description) > 100:
                    description = f"{description[:97]}..."

                options.append(discord.SelectOption(label=cmd_name, value=cmd_name, description=description))

        return sorted(options, key=lambda o: o.label)

    # Cogs and Command Categories
    async def _get_command_categories(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, commands.Command[Any, Any, Any]]]]:
        """Retrieves the command categories and their corresponding commands."""
        if self._category_cache:
            return self._category_cache, self.command_mapping or {}

        command_categories: dict[str, dict[str, str]] = {}
        command_mapping: dict[str, dict[str, commands.Command[Any, Any, Any]]] = {}

        for cog, mapping_commands in mapping.items():
            if cog and len(mapping_commands) > 0:
                # Attempt to extract the group using the cog's module name.
                cog_group = self._extract_cog_group(cog) or "extra"
                command_categories.setdefault(cog_group, {})
                command_mapping.setdefault(cog_group, {})
                for command in mapping_commands:
                    cmd = command
                    cmd_aliases = ", ".join(f"`{alias}`" for alias in cmd.aliases) if cmd.aliases else "`No aliases`"
                    command_categories[cog_group][cmd.name] = cmd_aliases
                    command_mapping[cog_group][cmd.name] = cmd

        self._category_cache = command_categories
        self.command_mapping = command_mapping
        return command_categories, command_mapping

    @staticmethod
    def _get_cog_groups() -> list[str]:
        """Retrieves a list of cog groups from the 'cogs' folder."""
        cogs_path = Path("./tux/cogs")
        return [d.name for d in cogs_path.iterdir() if d.is_dir() and d.name != "__pycache__"]

    @staticmethod
    def _extract_cog_group(cog: commands.Cog) -> str | None:
        """
        Extracts the cog group using the cog's module attribute.
        For example, if a cog's module is 'tux.cogs.admin.some_cog', this returns 'admin'.
        """
        module = getattr(cog, "__module__", "")
        parts = module.split(".")

        # Assuming the structure is: tux.cogs.<group>...
        if len(parts) >= 3 and parts[1].lower() == "cogs":
            return parts[2].lower()
        return None

    async def _create_main_view(self) -> HelpView:
        """Creates the main help view with category selection."""
        view = HelpView(self)

        # Add category select
        category_options = await self._create_category_options()
        category_select = HelpSelectMenu(self, category_options, "Select a category")
        view.add_item(category_select)

        # Add close button
        view.add_item(CloseButton())

        return view

    async def _create_category_view(self, category: str) -> HelpView:
        """Creates a view for a specific category with command selection."""
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
        """Creates a view for command details with back button."""
        view = HelpView(self)

        # Add back button and close button
        view.add_item(BackButton(self))
        view.add_item(CloseButton())

        return view

    async def _create_main_embed(self) -> discord.Embed:
        """Creates the main help embed."""
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
        """Creates an embed for a specific category."""
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
        """Creates an embed for a specific command."""
        if not self.current_category or not self.command_mapping:
            return self._embed_base("Error", "Command not found")

        command = self.command_mapping[self.current_category].get(command_name)
        if not command:
            return self._embed_base("Error", "Command not found")

        prefix = await self._get_prefix()
        embed = self._embed_base(
            title=f"{prefix}{command.qualified_name}",
            description=f"> {command.help or 'No documentation available.'}",
        )

        await self._add_command_help_fields(embed, command)

        if flag_details := self._format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        return embed

    async def _add_bot_help_fields(self, embed: discord.Embed) -> None:
        """Adds additional help information about the bot."""
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
            value=f"Flags in `[]` are optional. Most flags have aliases that can be used.\n> e.g. `{prefix}ban @user spamming` or `{prefix}b @user spamming -silent true`",
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
            value=f"-# Running {bot_name_display} version `{CONFIG.BOT_VERSION}` in `{environment}` mode | {owner_info}",
            inline=False,
        )

    # Event handlers for UI components
    async def on_category_select(self, interaction: discord.Interaction, category: str) -> None:
        """Handles when a category is selected from the dropdown."""
        self.current_category = category
        self.current_page = "category"

        embed = await self._create_category_embed(category)
        view = await self._create_category_view(category)

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)

    async def on_command_select(self, interaction: discord.Interaction, command_name: str) -> None:
        """Handles when a command is selected from the dropdown."""
        self.current_page = "command"

        embed = await self._create_command_embed(command_name)
        view = await self._create_command_view()

        if interaction.message:
            await interaction.message.edit(embed=embed, view=view)

    async def on_back_button(self, interaction: discord.Interaction) -> None:
        """Handles when the back button is clicked."""
        if not interaction.message:
            return

        if self.current_page == "command" and self.current_category:
            # Go back to category page
            self.current_page = "category"
            embed = await self._create_category_embed(self.current_category)
            view = await self._create_category_view(self.current_category)
        else:
            # Go back to main page
            self.current_page = "main"
            self.current_category = None
            embed = await self._create_main_embed()
            view = await self._create_main_view()

        await interaction.message.edit(embed=embed, view=view)

    # Sending Help Messages
    async def send_bot_help(self, mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]) -> None:
        """Sends help messages for the bot with custom pagination."""
        await self._get_command_categories(mapping)

        embed = await self._create_main_embed()
        view = await self._create_main_view()

        self.message = await self.get_destination().send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Sends a help message for a specific cog."""
        prefix = await self._get_prefix()
        embed = self._embed_base(f"{cog.qualified_name} Commands")

        for command in cog.get_commands():
            self._add_command_field(embed, command, prefix)

            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    self._add_command_field(embed, subcommand, prefix)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, Any, Any]) -> None:
        """Sends a help message for a specific command."""
        prefix = await self._get_prefix()

        embed = self._embed_base(
            title=f"{prefix}{command.qualified_name}",
            description=f"> {command.help or 'No documentation available.'}",
        )

        await self._add_command_help_fields(embed, command)

        if flag_details := self._format_flag_details(command):
            embed.add_field(name="Flags", value=f"```\n{flag_details}\n```", inline=False)

        view = HelpView(self)
        view.add_item(CloseButton())

        await self.get_destination().send(embed=embed, view=view)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """Sends a help message for a specific command group."""
        prefix = await self._get_prefix()

        # Create the main embed for the group command itself
        embed = self._embed_base(f"{group.name}", f"> {group.help or 'No documentation available.'}")
        await self._add_command_help_fields(embed, group)

        # Add subcommands to the embed
        for command in sorted(group.commands, key=lambda x: x.name):
            self._add_command_field(embed, command, prefix)

        view = HelpView(self)
        view.add_item(CloseButton())

        await self.get_destination().send(embed=embed, view=view)

    async def send_error_message(self, error: str) -> None:
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
