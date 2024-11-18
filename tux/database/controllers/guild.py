from prisma.models import Guild
from tux.database.client import db


class GuildController:
    def __init__(self):
        self.table = db.guild
        self.guild_config = db.guildconfig

    async def get_guild_by_id(self, guild_id: int) -> Guild | None:
        return await self.table.find_first(where={"guild_id": guild_id})

    async def insert_guild_by_id(self, guild_id: int) -> Guild:
        return await self.table.create(
            data={
                "guild_id": guild_id,
                "guild_config": {
                    "connect_or_create": {"where": {"guild_id": guild_id}, "create": {"guild_id": guild_id}},
                },
            },
        )

    async def delete_guild_by_id(self, guild_id: int) -> None:
        await self.table.delete(where={"guild_id": guild_id})

    async def get_all_guilds(self) -> list[Guild]:
        return await self.table.find_many()

    async def get_guild_onboarding_status(self, guild_id: int) -> bool:
        guild = await self.get_guild_by_id(guild_id)
        return guild.onboarding_completed if guild else False
