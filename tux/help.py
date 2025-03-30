import asyncio
from collections.abc import Awaitable, Mapping
from pathlib import Path
from typing import Any, get_type_hints

import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu
from reactionmenu.abc import Page
from reactionmenu.views_menu import ViewSelect

from tux.ui.embeds import EmbedCreator
from tux.utils.config import CONFIG
from tux.utils.constants import CONST


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
        self._prefix_cache: dict[int | None, str] = {}
        self._category_cache: dict[str, dict[str, str]] = {}

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
                if flag.aliases:
                    flag_str += f" ({', '.join(flag.aliases)})"
                flag_str += f"\n\t{flag.description or 'No description provided'}"
                if flag.default is not discord.utils.MISSING:
                    flag_str += f"\n\tDefault: {flag.default}"
                flag_details.append(flag_str)

        return "\n\n".join(flag_details)

    @staticmethod
    def _format_flag_name(flag: commands.Flag) -> str:
        """Formats the flag name based on whether it is required."""
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

    # Pages and Select Options
    async def _create_select_options(
        self,
        command_categories: dict[str, dict[str, str]],
        menu: ViewMenu,
    ) -> dict[discord.SelectOption, list[Page]]:
        """
        Creates select options for the help menu by iterating over the keys in the
        cached command categories. This approach ensures that even categories without
        a corresponding folder (e.g. "extra") are included.
        """
        select_options: dict[discord.SelectOption, list[Page]] = {}
        prefix: str = await self._get_prefix()

        # Iterate over the keys in command_categories
        tasks: list[Awaitable[tuple[str, Page]]] = [
            self._create_page(cog_group, command_categories, menu, prefix)
            for cog_group in command_categories
            if any(command_categories[cog_group].values())
        ]

        select_options_data: list[tuple[str, Page]] = await asyncio.gather(*tasks)

        category_emoji_map = {
            "info": "🔍",
            "moderation": "🛡",
            "utility": "🔧",
            "admin": "👑",
            "fun": "🎉",
            "levels": "📈",
            "services": "🔌",
        }

        for cog_group, page in select_options_data:
            emoji = category_emoji_map.get(cog_group, "❓")
            select_options[discord.SelectOption(label=cog_group.capitalize(), emoji=emoji)] = [page]

        return select_options

    async def _create_page(
        self,
        cog_group: str,
        command_categories: dict[str, dict[str, str]],
        menu: ViewMenu,
        prefix: str,
    ) -> tuple[str, Page]:
        embed: discord.Embed = self._embed_base(f"{cog_group.capitalize()} Commands")
        embed.set_footer(
            text=f"Use {prefix}help <command> or <subcommand> to learn about it.",
        )

        sorted_commands: list[tuple[str, str]] = sorted(command_categories[cog_group].items())
        description: str = "\n".join(f"**`{prefix}{cmd}`** | {command_list}" for cmd, command_list in sorted_commands)
        embed.description = description
        page: Page = Page(embed=embed)
        menu.add_page(embed)

        return cog_group, page

    @staticmethod
    def _add_navigation_and_selection(menu: ViewMenu, select_options: dict[discord.SelectOption, list[Page]]) -> None:
        """Adds navigation buttons and select options to the help menu."""
        menu.add_select(ViewSelect(title="🗃️ Select a category", options=select_options))
        menu.add_button(
            ViewButton(label="Close Menu", style=discord.ButtonStyle.danger, custom_id=ViewButton.ID_END_SESSION),
        )

    # Cogs and Command Categories
    async def _add_cog_pages(
        self,
        menu: ViewMenu,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> None:
        """Adds pages for each cog category to the help menu."""
        command_categories = await self._get_command_categories(mapping)

        # Instead of using filesystem folders, iterate over cached categories.
        select_options = await self._create_select_options(command_categories, menu)
        self._add_navigation_and_selection(menu, select_options)

    async def _get_command_categories(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ) -> dict[str, dict[str, str]]:
        """Retrieves the command categories and their corresponding commands."""
        if self._category_cache:
            return self._category_cache  # Return cached categories if available

        command_categories: dict[str, dict[str, str]] = {}

        for cog, mapping_commands in mapping.items():
            if cog and len(mapping_commands) > 0:
                # Attempt to extract the group using the cog's module name.
                cog_group = self._extract_cog_group(cog) or "extra"
                command_categories.setdefault(cog_group, {})
                for command in mapping_commands:
                    if command.aliases:
                        cmd_aliases = ", ".join(f"`{alias}`" for alias in command.aliases)
                    else:
                        cmd_aliases = "`No aliases`"
                    command_categories[cog_group][command.name] = cmd_aliases

        self._category_cache = command_categories  # Cache the results
        return command_categories

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

    # Sending Help Messages
    async def send_bot_help(self, mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]) -> None:
        """Sends help messages for the bot with pagination based on the folder it is in."""
        menu = ViewMenu(
            self.context,
            menu_type=ViewMenu.TypeEmbed,
            all_can_click=True,
            delete_on_timeout=True,
            timeout=180,
            show_page_director=False,
        )

        # TODO: Make help command more customizable
        if CONFIG.BOT_NAME != "Tux":
            logger.info("Bot name is not Tux, using different help message.")
            embed = self._embed_base(
                "Hello! Welcome to the help command.",
                f"{CONFIG.BOT_NAME} is an self hosted instance of Tux. The bot is written in Python using discord.py.\n\nIf you enjoy using {CONFIG.BOT_NAME}, consider contributing to the original project.",
            )
        else:
            embed = self._embed_base(
                "Hello! Welcome to the help command.",
                "Tux is an all-in-one bot by the All Things Linux Discord server. The bot is written in Python using discord.py, and we are actively seeking contributors.",
            )

        await self._add_bot_help_fields(embed)
        menu.add_page(embed)
        await self._add_cog_pages(menu, mapping)

        await menu.start()

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
            value=f"Use `{prefix}help <command>` or `{prefix}help <subcommand>` to learn about a specific command.\n> e.g. `{prefix}help ban` or `{prefix}h dev load_cog`",
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
        environment = "dev" if CONFIG.DEV else "prod"
        owner_info = f"Bot Owner: <@{CONFIG.BOT_OWNER_ID}>" if not CONFIG.HIDE_BOT_OWNER and CONFIG.BOT_OWNER_ID else ""

        embed.add_field(
            name="Bot Instance",
            value=f"-# Running {bot_name_display} version `{CONFIG.BOT_VERSION}` in `{environment}` mode | {owner_info}",
            inline=False,
        )

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

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, Any, Any]) -> None:
        """Sends a help message for a specific command group."""
        prefix = await self._get_prefix()

        # Create a menu for pagination
        menu = ViewMenu(
            self.context,
            menu_type=ViewMenu.TypeEmbed,
            delete_on_timeout=True,
            timeout=180,
            show_page_director=False,
        )

        # Create the main embed for the group command itself
        main_embed = self._embed_base(f"{group.name}", f"> {group.help or 'No documentation available.'}")
        await self._add_command_help_fields(main_embed, group)

        # Add the main embed as the first page
        menu.add_page(main_embed)

        # Create separate embeds for subcommands, with a maximum of 24 fields per embed
        # (leaving room for potentially adding a navigation hint field)
        commands_list = list(group.commands)
        total_commands = len(commands_list)

        if total_commands > 0:
            # If few commands, add them to the main embed
            if total_commands <= 24:
                for command in commands_list:
                    self._add_command_field(main_embed, command, prefix)
            else:
                # Create multiple pages for subcommands
                for i in range(0, total_commands, 24):
                    batch = commands_list[i : i + 24]
                    subcommand_embed = self._embed_base(
                        f"{group.name} Subcommands (Page {i // 24 + 1})",
                        f"Showing subcommands {i + 1}-{min(i + 24, total_commands)} of {total_commands}",
                    )

                    for command in batch:
                        self._add_command_field(subcommand_embed, command, prefix)

                    menu.add_page(subcommand_embed)

        # Always add at least the end session button first
        menu.add_button(ViewButton.end_session())

        # Add navigation buttons only if we have multiple pages
        if hasattr(menu, "pages") and menu.pages is not None and len(menu.pages) > 1:
            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())

        await menu.start()

    async def send_error_message(self, error: str) -> None:
        """Sends an error message."""

        logger.warning(f"An error occurred while sending a help message: {error}")

        embed = EmbedCreator.create_embed(
            EmbedCreator.ERROR,
            user_name=self.context.author.name,
            user_display_avatar=self.context.author.display_avatar.url,
            description=error,
        )

        await self.get_destination().send(embed=embed, delete_after=30)
