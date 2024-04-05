from prisma.models import Notes, Users
from tux.database.client import db


class UsersController:
    def __init__(self):
        self.table = db.users

    async def find_users(self) -> list[Users]:
        return await self.table.find_many()

    async def find_user(self, user_id: int) -> Users | None:
        return await self.table.find_first(where={"id": user_id})


class NotesController:
    def __init__(self):
        self.table = db.notes

    async def find_notes(self) -> list[Notes]:
        return await self.table.find_many()
