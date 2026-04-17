"""Permission and Discord check failures."""

from discord import app_commands
from discord.ext import commands

from .base import TuxError

__all__ = [
    "TuxAppCommandPermissionLevelError",
    "TuxPermissionDeniedError",
    "TuxPermissionError",
    "TuxPermissionLevelError",
]


class TuxPermissionError(TuxError):
    """Base exception for permission-related errors."""


class TuxPermissionLevelError(TuxPermissionError):
    """Raised when a user doesn't have the required permission rank."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


class TuxAppCommandPermissionLevelError(TuxPermissionError):
    """Raised when a user doesn't have the required permission rank for an app command."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


class TuxPermissionDeniedError(
    TuxPermissionError,
    commands.CheckFailure,
    app_commands.CheckFailure,
):
    """Raised when a user doesn't have permission to run a command (dynamic system).

    Inherits from both commands.CheckFailure and app_commands.CheckFailure to ensure
    proper error handling for both prefix and app commands in discord.py.
    """

    def __init__(
        self,
        required_rank: int,
        user_rank: int,
        command_name: str | None = None,
    ) -> None:
        """Initialize the permission denied error.

        Parameters
        ----------
        required_rank : int
            The minimum permission rank required to run the command.
        user_rank : int
            The actual permission rank of the user.
        command_name : str, optional
            The name of the command that was attempted, by default None.
        """
        self.required_rank = required_rank
        self.user_rank = user_rank
        self.command_name = command_name

        # Unconfigured: no permission rank assigned for this command (0/0)
        if required_rank == 0 and user_rank == 0:
            if command_name:
                message = f"Command `{command_name}` has not been configured (no permission rank assigned)."
            else:
                message = (
                    "Command has not been configured (no permission rank assigned)."
                )
        elif command_name:
            message = f"You need permission rank **{required_rank}** to use `{command_name}`. Your rank: **{user_rank}**"
        else:
            message = f"You need permission rank **{required_rank}**. Your rank: **{user_rank}**"

        # Initialize all parent classes
        TuxPermissionError.__init__(self, message)
        commands.CheckFailure.__init__(self, message)
        app_commands.CheckFailure.__init__(self, message)
