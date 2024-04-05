from enum import Enum

from prisma.models import Infractions, Notes, Snippets, Users
from tux.database.client import db


class InfractionType(Enum):
    BAN = "ban"
    WARN = "warn"
    KICK = "kick"
    TIMEOUT = "timeout"


class UsersController:
    def __init__(self):
        self.table = db.users

    async def get_all_users(self) -> list[Users]:
        return await self.table.find_many()

    async def get_user_by_id(self, user_id: int) -> Users | None:
        return await self.table.find_first(where={"id": user_id})


class InfractionsController:
    def __init__(self):
        self.table = db.infractions

    async def get_all_infractions(self) -> list[Infractions]:
        return await self.table.find_many()

    async def get_infraction_by_id(self, infraction_id: int) -> Infractions | None:
        return await self.table.find_first(where={"id": infraction_id})

    async def create_infraction(
        self,
        infraction_id: int,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
    ) -> Infractions:
        return await self.table.create(
            data={
                "id": infraction_id,
                "user_id": user_id,
                "moderator_id": moderator_id,
                "infraction_type": infraction_type.value,
                "infraction_reason": infraction_reason,
            }
        )

    async def delete_infraction(self, infraction_id: int) -> None:
        await self.table.delete(where={"id": infraction_id})

    async def update_infraction(
        self, infraction_id: int, infraction_reason: str
    ) -> Infractions | None:
        return await self.table.update(
            where={"id": infraction_id},
            data={"infraction_reason": infraction_reason},
        )


class NotesController:
    def __init__(self):
        self.table = db.notes

    async def get_all_notes(self) -> list[Notes]:
        return await self.table.find_many()

    async def get_note_by_id(self, note_id: int) -> Notes | None:
        return await self.table.find_first(where={"id": note_id})


class SnippetsController:
    def __init__(self):
        self.table = db.snippets

    async def get_all_snippets(self) -> list[Snippets]:
        return await self.table.find_many()

    async def get_snippet_by_name(self, name: str) -> Snippets | None:
        return await self.table.find_first(where={"name": name})

    async def create_snippet(self, name: str, content: str) -> Snippets:
        return await self.table.create(
            data={
                "name": name,
                "content": content,
            }
        )

    async def delete_snippet(self, name: str) -> None:
        await self.table.delete(where={"name": name})

    async def update_snippet(self, name: str, content: str) -> Snippets | None:
        return await self.table.update(
            where={"name": name},
            data={"content": content},
        )
