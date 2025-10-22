"""Help system data management."""

from __future__ import annotations

from typing import Any

from discord.ext import commands

from .utils import create_cog_category_mapping


class HelpData:
    """Manages help command data retrieval and caching."""

    def __init__(self, bot: commands.Bot | commands.AutoShardedBot) -> None:
        """Initialize the help data manager.

        Parameters
        ----------
        bot : commands.Bot | commands.AutoShardedBot
            The Discord bot instance to manage help data for.
        """
        self.bot = bot
        self._prefix_cache: dict[int | None, str] = {}
        self._category_cache: dict[str, dict[str, str]] = {}
        self.command_mapping: dict[str, dict[str, commands.Command[Any, Any, Any]]] | None = None

    async def get_prefix(self, ctx: commands.Context[Any]) -> str:
        """
        Get command prefix for the current context.

        Returns
        -------
        str
            The command prefix for the context.
        """
        guild_id = ctx.guild.id if ctx.guild else None

        if guild_id in self._prefix_cache:
            return self._prefix_cache[guild_id]

        prefix = ctx.clean_prefix
        self._prefix_cache[guild_id] = prefix
        return prefix

    async def get_command_categories(self) -> dict[str, dict[str, str]]:
        """
        Get categorized commands mapping.

        Returns
        -------
        dict[str, dict[str, str]]
            Dictionary mapping categories to their commands.
        """
        if self._category_cache:
            return self._category_cache

        # Create proper mapping for create_cog_category_mapping
        mapping: dict[commands.Cog | None, list[commands.Command[Any, Any, Any]]] = {}

        for cog in self.bot.cogs.values():
            cog_commands = [cmd for cmd in cog.get_commands() if await self._can_run_command(cmd)]
            if cog_commands:
                mapping[cog] = cog_commands

        # Add commands without cogs
        no_cog_commands = [cmd for cmd in self.bot.commands if cmd.cog is None and await self._can_run_command(cmd)]
        if no_cog_commands:
            mapping[None] = no_cog_commands

        # Store both category cache and command mapping
        self._category_cache, self.command_mapping = create_cog_category_mapping(mapping)
        return self._category_cache

    async def _can_run_command(self, command: commands.Command[Any, Any, Any]) -> bool:
        """
        Check if command can be run by checking basic requirements.

        Returns
        -------
        bool
            True if the command is not hidden and is enabled, False otherwise.
        """
        try:
            return not command.hidden and command.enabled
        except Exception:
            return False

    def find_command(self, command_name: str) -> commands.Command[Any, Any, Any] | None:
        """
        Find a command by name.

        Returns
        -------
        commands.Command[Any, Any, Any] | None
            The command if found, None otherwise.
        """
        # First try direct lookup
        if found := self.bot.get_command(command_name):
            return found

        # Then search in command mapping if available
        if self.command_mapping:
            for category_commands in self.command_mapping.values():
                if command_name in category_commands:
                    return category_commands[command_name]

        return None

    def find_parent_command(self, subcommand_name: str) -> tuple[str, commands.Command[Any, Any, Any]] | None:
        """
        Find parent command for a subcommand.

        Returns
        -------
        tuple[str, commands.Command[Any, Any, Any]] | None
            Tuple of (parent_name, subcommand) if found, None otherwise.
        """
        for command in self.bot.walk_commands():
            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    if subcommand.name == subcommand_name or subcommand_name in subcommand.aliases:
                        return command.qualified_name, subcommand
        return None

    def paginate_subcommands(
        self,
        command: commands.Group[Any, Any, Any],
        page_size: int = 10,
    ) -> list[list[commands.Command[Any, Any, Any]]]:
        """
        Paginate subcommands into pages.

        Returns
        -------
        list[list[commands.Command[Any, Any, Any]]]
            List of pages, each containing up to page_size subcommands.
        """
        subcommands = list(command.commands)
        return [subcommands[i : i + page_size] for i in range(0, len(subcommands), page_size)]
