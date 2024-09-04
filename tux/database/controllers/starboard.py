from datetime import datetime

from prisma.models import Guild, Starboard, StarboardMessage
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
        """
        Get a starboard by guild ID.

        Returns:
        - Starboard: The starboard if found.
        - None: If no starboard exists for the given guild ID.
        """
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
        """
        Delete a starboard by guild ID.

        Returns:
        - Starboard: The deleted starboard if found and deleted successfully.
        - None: If no starboard exists for the given guild ID.
        """
        return await self.table.delete(where={"guild_id": guild_id})


class StarboardMessageController:
    def __init__(self):
        self.table = db.starboardmessage
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild | None:
        guild = await self.guild_table.find_unique(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def get_starboard_message(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """
        Get a starboard message by message ID and guild ID.

        Returns:
        - StarboardMessage: The starboard message if found.
        - None: If no starboard message exists for the given message ID and guild ID.
        """
        return await self.table.find_unique(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
        )

    async def create_or_update_starboard_message(
        self,
        message_id: int,
        message_content: str,
        message_expires_at: datetime,
        message_channel_id: int,
        message_user_id: int,
        message_guild_id: int,
        star_count: int,
        starboard_message_id: int,
    ) -> StarboardMessage:
        await self.ensure_guild_exists(message_guild_id)

        return await self.table.upsert(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": message_guild_id}},
            data={
                "create": {
                    "message_id": message_id,
                    "message_content": message_content,
                    "message_expires_at": message_expires_at,
                    "message_channel_id": message_channel_id,
                    "message_user_id": message_user_id,
                    "message_guild_id": message_guild_id,
                    "star_count": star_count,
                    "starboard_message_id": starboard_message_id,
                },
                "update": {
                    "message_content": message_content,
                    "message_expires_at": message_expires_at,
                    "message_channel_id": message_channel_id,
                    "message_user_id": message_user_id,
                    "star_count": star_count,
                    "starboard_message_id": starboard_message_id,
                },
            },
        )

    async def delete_starboard_message(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """
        Delete a starboard message by message ID and guild ID.

        Returns:
        - StarboardMessage: The deleted starboard message if found and deleted successfully.
        - None: If no starboard message exists for the given message ID and guild ID.
        """
        return await self.table.delete(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
        )

    async def get_all_starboard_messages(self, guild_id: int) -> list[StarboardMessage]:
        return await self.table.find_many(where={"message_guild_id": guild_id})

    async def update_star_count(self, message_id: int, guild_id: int, new_star_count: int) -> StarboardMessage | None:
        """
        Update the star count for a message.

        Returns:
        - StarboardMessage: The updated message if found and updated successfully.
        - None: If the message is not found or the update fails.
        """
        return await self.table.update(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
            data={"star_count": new_star_count},
        )

    async def get_starboard_message_by_id(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """
        Get a starboard message by its ID and guild ID.

        A "starboard message" is the response by the bot, not the original message.

        Args:
            starboard_message_id (int): The ID of the starboard message.
            guild_id (int): The ID of the guild.

        Returns:
            StarboardMessage | None: The starboard message if found, otherwise None.
        """
        return await self.table.find_first(where={"message_id": message_id, "message_guild_id": guild_id})
