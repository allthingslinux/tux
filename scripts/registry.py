"""
Command Registry Infrastructure

Provides OOP classes for managing CLI commands in a clean, extensible way.
"""

from collections.abc import Callable


class Command:
    """Represents a single CLI command."""

    def __init__(self, name: str, func: Callable[[], None], help_text: str):
        self.name = name
        self.func = func
        self.help_text = help_text


class CommandGroup:
    """Represents a group of related CLI commands."""

    def __init__(self, name: str, help_text: str, rich_help_panel: str):
        self.name = name
        self.help_text = help_text
        self.rich_help_panel = rich_help_panel
        self._commands: dict[str, Command] = {}

    def add_command(self, command: Command) -> None:
        """Add a command to this group."""
        self._commands[command.name] = command

    def get_commands(self) -> dict[str, Command]:
        """Get all commands in this group."""
        return self._commands.copy()

    def get_command(self, name: str) -> Command | None:
        """Get a specific command by name."""
        return self._commands.get(name)


class CommandRegistry:
    """Registry for managing CLI commands in an OOP way."""

    def __init__(self):
        self._groups: dict[str, CommandGroup] = {}
        self._commands: dict[str, Command] = {}

    def register_group(self, group: CommandGroup) -> None:
        """Register a command group."""
        self._groups[group.name] = group

    def register_command(self, command: Command) -> None:
        """Register an individual command."""
        self._commands[command.name] = command

    def get_groups(self) -> dict[str, CommandGroup]:
        """Get all registered command groups."""
        return self._groups.copy()

    def get_commands(self) -> dict[str, Command]:
        """Get all registered individual commands."""
        return self._commands.copy()

    def get_group(self, name: str) -> CommandGroup | None:
        """Get a specific command group by name."""
        return self._groups.get(name)

    def get_command(self, name: str) -> Command | None:
        """Get a specific individual command by name."""
        return self._commands.get(name)
