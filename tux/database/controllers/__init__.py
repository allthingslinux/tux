from .cases import CaseController
from .notes import NoteController
from .reminders import ReminderController
from .snippets import SnippetController


class DatabaseController:
    def __init__(self):
        self.cases = CaseController()
        self.notes = NoteController()
        self.snippets = SnippetController()
        self.reminders = ReminderController()


db_controller = DatabaseController()
