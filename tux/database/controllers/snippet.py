import datetime

from prisma.models import Guild, Snippet
from tux.database.client import db


class SnippetController:
    def __init__(self) -> None:
        self.table = db.snippet
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild | None:
        guild = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def get_all_snippets(self) -> list[Snippet]:
        return await self.table.find_many()

    async def get_all_snippets_by_guild_id(self, guild_id: int) -> list[Snippet]:
        return await self.table.find_many(where={"guild_id": guild_id})

    async def get_all_snippets_sorted(self, newestfirst: bool = True) -> list[Snippet]:
        return await self.table.find_many(
            order={"snippet_created_at": "desc" if newestfirst else "asc"},
        )

    async def get_snippet_by_name(self, snippet_name: str) -> Snippet | None:
        return await self.table.find_first(where={"snippet_name": {"contains": snippet_name, "mode": "insensitive"}})

    async def get_snippet_by_name_and_guild_id(
        self,
        snippet_name: str,
        guild_id: int,
    ) -> Snippet | None:
        return await self.table.find_first(
            where={"snippet_name": {"equals": snippet_name, "mode": "insensitive"}, "guild_id": guild_id},
        )

    async def create_snippet(
        self,
        snippet_name: str,
        snippet_content: str,
        snippet_created_at: datetime.datetime,
        snippet_user_id: int,
        guild_id: int,
    ) -> Snippet:
        await self.ensure_guild_exists(guild_id)

        return await self.table.create(
            data={
                "snippet_name": snippet_name,
                "snippet_content": snippet_content,
                "snippet_created_at": snippet_created_at,
                "snippet_user_id": snippet_user_id,
                "guild_id": guild_id,
            },
        )

    async def delete_snippet_by_id(self, snippet_id: int) -> None:
        await self.table.delete(where={"snippet_id": snippet_id})

    async def update_snippet_by_id(self, snippet_id: int, snippet_content: str) -> Snippet | None:
        return await self.table.update(
            where={"snippet_id": snippet_id},
            data={"snippet_content": snippet_content},
        )

    async def increment_snippet_uses(self, snippet_id: int) -> Snippet | None:
        snippet = await self.table.find_first(where={"snippet_id": snippet_id})
        if snippet is None:
            return None

        return await self.table.update(
            where={"snippet_id": snippet_id},
            data={"uses": snippet.uses + 1},
        )

    async def lock_snippet_by_id(self, snippet_id: int) -> Snippet | None:
        return await self.table.update(
            where={"snippet_id": snippet_id},
            data={"locked": True},
        )

    async def unlock_snippet_by_id(self, snippet_id: int) -> Snippet | None:
        return await self.table.update(
            where={"snippet_id": snippet_id},
            data={"locked": False},
        )

    async def toggle_snippet_lock_by_id(self, snippet_id: int) -> Snippet | None:
        snippet = await self.table.find_first(where={"snippet_id": snippet_id})
        if snippet is None:
            return None

        return await self.table.update(
            where={"snippet_id": snippet_id},
            data={"locked": not snippet.locked},
        )
