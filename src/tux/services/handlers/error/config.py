"""Configuration and constants for error handling system."""

from dataclasses import dataclass

# Default message displayed to the user when an unhandled error occurs
# or when formatting a specific error message fails.
DEFAULT_ERROR_MESSAGE: str = "An unexpected error occurred. Please try again later."

# Default time in seconds before attempting to delete error messages sent
# via traditional (prefix) commands. This helps keep channels cleaner.
COMMAND_ERROR_DELETE_AFTER: int = 30

# Default time in seconds before deleting the 'Did you mean?' command suggestion message.
# This provides temporary assistance without persistent channel clutter.
SUGGESTION_DELETE_AFTER: int = 15


@dataclass
class ErrorHandlerConfig:
    """
    Configuration for the ErrorHandler.

    This dataclass encapsulates various settings that control the behavior
    of error handling, such as whether to delete error messages after a delay,
    how long to wait before deletion, and whether to suggest similar commands
    when a command is not found.
    """

    # Whether to automatically delete error messages after a delay (prefix commands only)
    delete_error_messages: bool = True

    # Time in seconds to wait before deleting error messages (prefix commands only)
    error_message_delete_after: int = COMMAND_ERROR_DELETE_AFTER

    # Whether to suggest similar commands when CommandNotFound occurs
    suggest_similar_commands: bool = True

    # Time in seconds to wait before deleting command suggestion messages
    suggestion_delete_after: int = SUGGESTION_DELETE_AFTER
