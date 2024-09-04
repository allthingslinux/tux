from prisma.models import Guild, Starboard
from tux.database.client import db


class StarboardController:
    def __init__(self):
        self.table = db.starboard
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild | None:
        guild = await self.guild_table.find_unique(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def get_all_starboards(self) -> list[Starboard]:
        return await self.table.find_many()

    async def get_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        return await self.table.find_unique(where={"guild_id": guild_id})

    async def create_or_update_starboard(
        self,
        guild_id: int,
        starboard_channel_id: int,
        starboard_emoji: str,
        starboard_threshold: int,
    ) -> Starboard:
        await self.ensure_guild_exists(guild_id)

        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "starboard_channel_id": starboard_channel_id,
                    "starboard_emoji": starboard_emoji,
                    "starboard_threshold": starboard_threshold,
                },
                "update": {
                    "starboard_channel_id": starboard_channel_id,
                    "starboard_emoji": starboard_emoji,
                    "starboard_threshold": starboard_threshold,
                },
            },
        )

    async def delete_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        return await self.table.delete(where={"guild_id": guild_id})
