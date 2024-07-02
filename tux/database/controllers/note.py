from prisma.models import Guild, Note
from tux.database.client import db


class NoteController:
    def __init__(self):
        self.table = db.note
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild | None:
        guild = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def get_all_notes(self) -> list[Note]:
        return await self.table.find_many()

    async def get_note_by_id(self, note_id: int) -> Note | None:
        return await self.table.find_first(where={"note_id": note_id})

    async def insert_note(
        self,
        note_target_id: int,
        note_moderator_id: int,
        note_content: str,
        guild_id: int,
    ) -> Note:
        await self.ensure_guild_exists(guild_id)

        return await self.table.create(
            data={
                "note_target_id": note_target_id,
                "note_moderator_id": note_moderator_id,
                "note_content": note_content,
                "guild_id": guild_id,
            },
        )

    async def delete_note_by_id(self, note_id: int) -> None:
        await self.table.delete(where={"note_id": note_id})

    async def update_note_by_id(self, note_id: int, note_content: str) -> Note | None:
        return await self.table.update(
            where={"note_id": note_id},
            data={"note_content": note_content},
        )

    async def get_notes_by_target_id(self, target_id: int) -> list[Note]:
        return await self.table.find_many(where={"note_target_id": target_id})

    async def get_notes_by_moderator_id(self, moderator_id: int) -> list[Note]:
        return await self.table.find_many(where={"note_moderator_id": moderator_id})

    async def get_notes_by_guild_id(self, guild_id: int) -> list[Note]:
        return await self.table.find_many(where={"guild_id": guild_id})

    async def get_notes_by_target_id_and_guild_id(
        self,
        target_id: int,
        guild_id: int,
    ) -> list[Note]:
        return await self.table.find_many(where={"note_target_id": target_id, "guild_id": guild_id})

    async def get_notes_by_moderator_id_and_guild_id(
        self,
        moderator_id: int,
        guild_id: int,
    ) -> list[Note]:
        return await self.table.find_many(
            where={"note_moderator_id": moderator_id, "guild_id": guild_id},
        )

    async def get_notes_by_target_id_and_moderator_id(
        self,
        target_id: int,
        moderator_id: int,
    ) -> list[Note]:
        return await self.table.find_many(
            where={"note_target_id": target_id, "note_moderator_id": moderator_id},
        )

    async def get_notes_by_target_id_moderator_id_and_guild_id(
        self,
        target_id: int,
        moderator_id: int,
        guild_id: int,
    ) -> list[Note]:
        return await self.table.find_many(
            where={
                "note_target_id": target_id,
                "note_moderator_id": moderator_id,
                "guild_id": guild_id,
            },
        )
