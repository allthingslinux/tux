from .case import CaseController
from .guild import GuildController
from .guild_config import GuildConfigController
from .note import NoteController
from .reminder import ReminderController
from .snippet import SnippetController


class DatabaseController:
    def __init__(self):
        self.case = CaseController()
        self.note = NoteController()
        self.snippet = SnippetController()
        self.reminder = ReminderController()
        self.guild = GuildController()
        self.guild_config = GuildConfigController()


db_controller = DatabaseController()
