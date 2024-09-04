from .afk import AfkController
from .case import CaseController
from .guild import GuildController
from .guild_config import GuildConfigController
from .note import NoteController
from .reminder import ReminderController
from .snippet import SnippetController
from .starboard import StarboardController, StarboardMessageController


class DatabaseController:
    def __init__(self):
        self.case = CaseController()
        self.note = NoteController()
        self.snippet = SnippetController()
        self.reminder = ReminderController()
        self.guild = GuildController()
        self.guild_config = GuildConfigController()
        self.afk = AfkController()
        self.starboard = StarboardController()
        self.starboard_message = StarboardMessageController()
