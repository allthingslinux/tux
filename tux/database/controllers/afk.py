from prisma.models import AFKModel, Guild
from tux.database.client import db


class AfkController:
    def __init__(self) -> None:
        self.table = db.afkmodel
        self.guild = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild:
        guild = await self.guild.find_first(where={"guild_id": guild_id})

        if guild is None:
            return await self.guild.create(data={"guild_id": guild_id})

        return guild

    async def get_afk_member(self, member_id: int, *, guild_id: int) -> AFKModel | None:
        return await self.table.find_first(where={"member_id": member_id, "guild_id": guild_id})

    async def is_afk(self, member_id: int, *, guild_id: int) -> bool:
        entry = await self.get_afk_member(member_id, guild_id=guild_id)
        return entry is not None

    async def insert_afk(self, member_id: int, nickname: str, reason: str, guild_id: int) -> AFKModel:
        await self.ensure_guild_exists(guild_id)

        return await self.table.create(
            data={
                "member_id": member_id,
                "nickname": nickname,
                "reason": reason,
                "guild_id": guild_id,
            },
        )

    async def remove_afk(self, member_id: int) -> None:
        await self.table.delete(where={"member_id": member_id})
