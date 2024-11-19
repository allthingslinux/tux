# fmt: off
import contextlib
from collections.abc import Generator
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class MentionableTree(app_commands.CommandTree):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.application_commands: dict[int | None, list[app_commands.AppCommand]] = {}
        self.cache: dict[int | None, dict[app_commands.Command[Any, ..., Any] | commands.HybridCommand[Any, ..., Any] | str, str]] = {}

    async def sync(self, *, guild: discord.abc.Snowflake | None = None):
        """Method overwritten to store the commands."""
        ret = await super().sync(guild=guild)
        guild_id = guild.id if guild else None
        self.application_commands[guild_id] = ret
        self.cache.pop(guild_id, None)
        return ret

    async def fetch_commands(self, *, guild: discord.abc.Snowflake | None = None):
        """Method overwritten to store the commands."""
        ret = await super().fetch_commands(guild=guild)
        guild_id = guild.id if guild else None
        self.application_commands[guild_id] = ret
        self.cache.pop(guild_id, None)
        return ret

    async def get_or_fetch_commands(self, *, guild: discord.abc.Snowflake | None = None):
        """Method overwritten to store the commands."""
        try:
            return self.application_commands[guild.id if guild else None]
        except KeyError:
            return await self.fetch_commands(guild=guild)


    async def find_mention_for(
        self,
        command: app_commands.Command[Any, ..., Any] | commands.HybridCommand[Any, ..., Any] | str,
        *,
        guild: discord.abc.Snowflake | None = None,
    ) -> str | None:
        """Retrieves the mention of an AppCommand given a specific command name, and optionally, a guild.

        Parameters
        ----------
        name: Union[:class:`app_commands.Command`, :class:`commands.HybridCommand`, str]
            The command to retrieve the mention for.
        guild: Optional[:class:`discord.abc.Snowflake`]
            The scope (guild) from which to retrieve the commands from. If None is given or not passed,
            only the global scope will be searched, however the global scope will also be searched if
            a guild is passed.

        Returns
        -------
        str | None
            The command mention, if found.
        """

        guild_id = guild.id if guild else None
        with contextlib.suppress(KeyError):
            return self.cache[guild_id][command]

        # If a guild is given, and fallback to global is set to True, then we must also
        # check the global scope, as commands for both show in a guild.
        check_global = self.fallback_to_global is True and guild is not None

        if isinstance(command, str):
            # Try and find a command by that name. discord.py does not return children from tree.get_command, but
            # using walk_commands and utils.get is a simple way around that.
            _command = discord.utils.get(self.walk_commands(guild=guild), qualified_name=command)

            if check_global and not _command:
                _command = discord.utils.get(self.walk_commands(), qualified_name=command)

        else:
            _command = command

        if not _command:
            return None

        local_commands = await self.get_or_fetch_commands(guild=guild)
        app_command_found = discord.utils.get(local_commands, name=(_command.root_parent or _command).name)

        if check_global and not app_command_found:
            global_commands = await self.get_or_fetch_commands(guild=None)
            app_command_found = discord.utils.get(global_commands, name=(_command.root_parent or _command).name)

        if not app_command_found:
            return None

        mention = f"</{_command.qualified_name}:{app_command_found.id}>"
        self.cache.setdefault(guild_id, {})
        self.cache[guild_id][command] = mention
        return mention

    def _walk_children(self, commands: list[app_commands.Group | app_commands.Command[Any, ..., Any]]) -> Generator[app_commands.Command[Any, ..., Any], None, None]:
        for command in commands:
            if isinstance(command, app_commands.Group):
                yield from self._walk_children(command.commands)
            else:
                yield command

    async def walk_mentions(self, *, guild: discord.abc.Snowflake | None = None):
        """Gets all valid mentions for app commands in a specific guild.

        This takes into consideration group commands, it will only return mentions for
        the command's children, and not the parent as parents aren't mentionable.

        Parameters
        ----------
        guild: Optional[discord.Guild]
            The guild to get commands for. If not given, it will only return global commands.

        Yields
        ------
        Tuple[Union[:class:`app_commands.Command`, :class:`commands.HybridCommand`], str]

        """
        for command in self._walk_children(self.get_commands(guild=guild, type=discord.AppCommandType.chat_input)):
            mention = await self.find_mention_for(command, guild=guild)
            if mention:
                yield command, mention
        if guild and self.fallback_to_global is True:
            for command in self._walk_children(self.get_commands(guild=None, type=discord.AppCommandType.chat_input)):
                mention = await self.find_mention_for(command, guild=guild)
                if mention:
                    yield command, mention
                else:
                    logger.warning("Could not find a mention for command %s in the API. Are you out of sync?", command)
