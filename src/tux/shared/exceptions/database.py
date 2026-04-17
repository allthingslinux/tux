"""Database-related exceptions."""

from .base import TuxError

__all__ = [
    "TuxDatabaseConnectionError",
    "TuxDatabaseError",
    "TuxDatabaseMigrationError",
    "TuxDatabaseQueryError",
]


class TuxDatabaseError(TuxError):
    """Base exception for database-related errors."""


class TuxDatabaseConnectionError(TuxDatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Database connection failed",
        original_error: Exception | None = None,
    ) -> None:
        self.original_error = original_error
        super().__init__(message)


class TuxDatabaseMigrationError(TuxDatabaseError):
    """Raised when database migration fails."""


class TuxDatabaseQueryError(TuxDatabaseError):
    """Raised when a database query fails."""
