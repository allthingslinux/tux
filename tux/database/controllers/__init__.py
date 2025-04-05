"""Database Controllers Module.

This module provides a unified interface to all database controllers in the application.
It centralizes access to different database operations through a single DatabaseController class.
"""

from .afk import AfkController
from .case import CaseController
from .guild import GuildController
from .guild_config import GuildConfigController
from .levels import LevelsController
from .note import NoteController
from .reminder import ReminderController
from .snippet import SnippetController
from .starboard import StarboardController, StarboardMessageController


class DatabaseController:
    """Unified interface for all database operations.

    This class provides centralized access to all database controllers,
    making it easier to manage database operations throughout the application.

    Attributes
    ----------
    case : CaseController
        Controller for moderation cases
    note : NoteController
        Controller for user notes
    snippet : SnippetController
        Controller for custom snippets
    reminder : ReminderController
        Controller for user reminders
    guild : GuildController
        Controller for guild data
    guild_config : GuildConfigController
        Controller for guild configuration
    afk : AfkController
        Controller for AFK status
    starboard : StarboardController
        Controller for starboard functionality
    starboard_message : StarboardMessageController
        Controller for starboard messages
    levels : LevelsController
        Controller for member levels and XP

    Examples
    --------
    >>> db = DatabaseController()
    >>> # Get guild data
    >>> guild_data = await db.guild.get(guild_id=123456789)
    >>> # Create a moderation case
    >>> case = await db.case.create(guild_id=123456789, user_id=987654321)
    """

    def __init__(self):
        """Initialize the DatabaseController with all sub-controllers."""
        self.case = CaseController()
        self.note = NoteController()
        self.snippet = SnippetController()
        self.reminder = ReminderController()
        self.guild = GuildController()
        self.guild_config = GuildConfigController()
        self.afk = AfkController()
        self.starboard = StarboardController()
        self.starboard_message = StarboardMessageController()
        self.levels = LevelsController()
