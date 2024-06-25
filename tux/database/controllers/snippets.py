import datetime

from prisma.models import Snippet
from tux.database.client import db


class SnippetController:
    def __init__(self) -> None:
        self.table = db.snippet

    async def get_all_snippets(self) -> list[Snippet]:
        return await self.table.find_many()

    async def get_all_snippets_sorted(self, newestfirst: bool = True) -> list[Snippet]:
        return await self.table.find_many(order={"snippet_created_at": "desc" if newestfirst else "asc"})

    async def get_snippet_by_name(self, snippet_name: str) -> Snippet | None:
        return await self.table.find_first(where={"snippet_name": snippet_name})

    async def get_snippet_by_name_and_guild_id(self, snippet_name: str, guild_id: int) -> Snippet | None:
        return await self.table.find_first(where={"snippet_name": snippet_name, "guild_id": guild_id})

    async def create_snippet(
        self,
        snippet_name: str,
        snippet_content: str,
        snippet_created_at: datetime.datetime,
        snippet_user_id: int,
        guild_id: int,
    ) -> Snippet:
        return await self.table.create(
            data={
                "snippet_name": snippet_name,
                "snippet_content": snippet_content,
                "snippet_created_at": snippet_created_at,
                "snippet_user_id": snippet_user_id,
                "guild_id": guild_id,
            }
        )

    async def delete_snippet_by_id(self, snippet_id: int) -> None:
        await self.table.delete(where={"snippet_id": snippet_id})

    async def update_snippet_by_id(self, snippet_id: int, snippet_content: str) -> Snippet | None:
        return await self.table.update(where={"snippet_id": snippet_id}, data={"snippet_content": snippet_content})
