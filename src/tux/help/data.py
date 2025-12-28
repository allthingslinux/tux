"""Help system data management."""

from __future__ import annotations

from typing import Any

from discord.ext import commands
from loguru import logger

from tux.core.permission_system import RESTRICTED_COMMANDS, get_permission_system
from tux.shared.config import CONFIG

from .utils import create_cog_category_mapping


class HelpData:
    """Manages help command data retrieval and caching."""

    def __init__(
        self,
        bot: commands.Bot | commands.AutoShardedBot,
        ctx: commands.Context[Any] | None = None,
    ) -> None:
        """Initialize the help data manager.

        Parameters
        ----------
        bot : commands.Bot | commands.AutoShardedBot
            The Discord bot instance to manage help data for.
        ctx : commands.Context[Any] | None, optional
            The command context for permission checking. If None, all commands are shown.
        """
        self.bot = bot
        self.ctx = ctx
        self._prefix_cache: dict[int | None, str] = {}
        self._category_cache: dict[str, dict[str, str]] = {}
        self.command_mapping: (
            dict[str, dict[str, commands.Command[Any, Any, Any]]] | None
        ) = None

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
        # Note: We don't cache command categories per user since permissions can vary
        # Rebuilding ensures each user sees only commands they have permission for

        # Create proper mapping for create_cog_category_mapping
        mapping: dict[commands.Cog | None, list[commands.Command[Any, Any, Any]]] = {}

        for cog in self.bot.cogs.values():
            cog_commands = [
                cmd for cmd in cog.get_commands() if await self.can_run_command(cmd)
            ]
            if cog_commands:
                mapping[cog] = cog_commands

        # Add commands without cogs
        no_cog_commands = [
            cmd
            for cmd in self.bot.commands
            if cmd.cog is None and await self.can_run_command(cmd)
        ]
        if no_cog_commands:
            mapping[None] = no_cog_commands

        # Store both category cache and command mapping
        self._category_cache, self.command_mapping = create_cog_category_mapping(
            mapping,
        )
        return self._category_cache

    async def can_run_command(self, command: commands.Command[Any, Any, Any]) -> bool:
        """
        Check if command can be run by checking basic requirements and permissions.

        Returns
        -------
        bool
            True if the command is visible and the user has permission, False otherwise.
        """
        try:
            # Basic checks: hidden and enabled
            if command.hidden or not command.enabled:
                return False

            # If no context provided, show all commands (fallback)
            # DM context: show all commands (permissions don't apply in DMs)
            if not self.ctx or not self.ctx.guild:
                return True

            # Check if command is restricted (owner/sysadmin only)
            if command.name.lower() in RESTRICTED_COMMANDS:
                return self._is_owner_or_sysadmin()

            # Check if command uses permission system
            if self._uses_permission_system(command):
                return await self._check_permission_rank(command)
            # Commands without permission decorator are visible to all
            return True  # noqa: TRY300

        except Exception as e:
            logger.trace(f"Error checking command permission for {command.name}: {e}")
            # On error, default to hiding the command for safety
            return False

    def _is_owner_or_sysadmin(self) -> bool:
        """Check if the user is bot owner or sysadmin.

        Returns
        -------
        bool
            True if user is owner or sysadmin, False otherwise.
        """
        if not self.ctx:
            return False

        user_id = self.ctx.author.id
        bot = self.bot

        # Check if user is in bot owner_ids (includes owner + sysadmins if ALLOW_SYSADMINS_EVAL is enabled)
        if hasattr(bot, "owner_ids") and bot.owner_ids and user_id in bot.owner_ids:
            return True

        # Also check CONFIG directly for owner and sysadmins
        return (
            user_id == CONFIG.USER_IDS.BOT_OWNER_ID
            or user_id in CONFIG.USER_IDS.SYSADMINS
        )

    def _uses_permission_system(self, command: commands.Command[Any, Any, Any]) -> bool:
        """Check if a command uses the permission system decorator.

        Parameters
        ----------
        command : commands.Command[Any, Any, Any]
            The command to check.

        Returns
        -------
        bool
            True if command uses @requires_command_permission(), False otherwise.
        """
        # Check the callback itself first
        if hasattr(command.callback, "__uses_dynamic_permissions__"):
            return True

        # Check wrapped function if it exists (for decorated commands)
        wrapped = getattr(command.callback, "__wrapped__", None)
        return wrapped is not None and hasattr(wrapped, "__uses_dynamic_permissions__")

    async def _check_permission_rank(
        self,
        command: commands.Command[Any, Any, Any],
    ) -> bool:
        """Check if user has required permission rank for a command.

        Parameters
        ----------
        command : commands.Command[Any, Any, Any]
            The command to check permissions for.

        Returns
        -------
        bool
            True if user has permission, False otherwise.
        """
        if not self.ctx or not self.ctx.guild:
            return True  # DM context or no context

        try:
            permission_system = get_permission_system()

            # Bot owners and sysadmins bypass all permission checks
            if self._is_owner_or_sysadmin():
                return True

            # Guild owner bypass - server owners can always see commands
            # This ensures server owners can access config commands even before
            # permissions are set up, allowing them to configure the permission system
            if self.ctx.guild.owner_id == self.ctx.author.id:
                return True

            # Get command permission config from database
            command_name = command.qualified_name
            cmd_perm = await permission_system.get_command_permission(
                self.ctx.guild.id,
                command_name,
            )

            # If not configured, command is hidden (safe default)
            # Note: Server owners bypass this check above, so they can always see commands
            if cmd_perm is None:
                return False

            # Get user's permission rank and check if user meets required rank
            user_rank = await permission_system.get_user_permission_rank(self.ctx)
            return user_rank >= cmd_perm.required_rank  # noqa: TRY300
        except Exception as e:
            logger.trace(f"Error checking permission rank for {command.name}: {e}")
            # On error, default to hiding the command for safety
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

    def find_parent_command(
        self,
        subcommand_name: str,
    ) -> tuple[str, commands.Command[Any, Any, Any]] | None:
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
                    if (
                        subcommand.name == subcommand_name
                        or subcommand_name in subcommand.aliases
                    ):
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
        return [
            subcommands[i : i + page_size]
            for i in range(0, len(subcommands), page_size)
        ]
