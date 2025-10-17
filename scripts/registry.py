"""
Command Registry Infrastructure.

Provides OOP classes for managing CLI commands in a clean, extensible way.
"""

from collections.abc import Callable


class Command:
    """Represents a single CLI command.

    A simple data structure that encapsulates a CLI command with its
    name, function, and help text.

    Parameters
    ----------
    name : str
        The name of the command.
    func : Callable[..., None]
        The function that implements the command.
    help_text : str
        Help text describing what the command does.

    Attributes
    ----------
    name : str
        The command name.
    func : Callable[..., None]
        The command function.
    help_text : str
        Description of the command.
    """

    def __init__(self, name: str, func: Callable[..., None], help_text: str):
        """Initialize a Command instance.

        Parameters
        ----------
        name : str
            The name of the command.
        func : Callable[..., None]
            The function that implements the command.
        help_text : str
            Help text describing what the command does.
        """
        self.name = name
        self.func = func
        self.help_text = help_text


class CommandGroup:
    """Represents a group of related CLI commands.

    A collection of commands organized under a common name and help panel.
    Useful for grouping related functionality in CLI help output.

    Parameters
    ----------
    name : str
        The name of the command group.
    help_text : str
        Help text describing the group.
    rich_help_panel : str
        Rich help panel name for organizing commands in help output.

    Attributes
    ----------
    name : str
        The group name.
    help_text : str
        Description of the group.
    rich_help_panel : str
        Rich help panel identifier.
    _commands : dict[str, Command]
        Internal dictionary of commands in this group.
    """

    def __init__(self, name: str, help_text: str, rich_help_panel: str):
        """Initialize a CommandGroup instance.

        Parameters
        ----------
        name : str
            The name of the command group.
        help_text : str
            Help text describing the group.
        rich_help_panel : str
            Rich help panel name for organizing commands in help output.
        """
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
    """Registry for managing CLI commands in an OOP way.

    A central registry that manages both individual commands and command groups.
    Provides methods for registering and retrieving commands and groups.

    Attributes
    ----------
    _groups : dict[str, CommandGroup]
        Internal dictionary of registered command groups.
    _commands : dict[str, Command]
        Internal dictionary of registered individual commands.
    """

    def __init__(self):
        """Initialize a CommandRegistry instance.

        Creates empty dictionaries for storing command groups and individual commands.
        """
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
