from .infractions import InfractionsController
from .notes import NotesController
from .reminders import RemindersController
from .roles import RolesController
from .snippets import SnippetsController
from .user_roles import UserRolesController
from .users import UsersController


class DatabaseController:
    def __init__(self):
        self.users = UsersController()
        self.infractions = InfractionsController()
        self.notes = NotesController()
        self.snippets = SnippetsController()
        self.reminders = RemindersController()
        self.roles = RolesController()
        self.user_roles = UserRolesController()
