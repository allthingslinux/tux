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
        """
        Get all starboards.

        Returns
        -------
        list[Starboard]:
            A list of all starboards.
        """

        return await self.table.find_many()

    async def get_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        """
        Get a starboard by guild ID.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        Starboard | None:
            The starboard if found.
            None if no starboard exists for the given guild ID.
        """

        return await self.table.find_unique(where={"guild_id": guild_id})

    async def create_or_update_starboard(
        self,
        guild_id: int,
        starboard_channel_id: int,
        starboard_emoji: str,
        starboard_threshold: int,
    ) -> Starboard:
        """
        Create or update a starboard.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        starboard_channel_id : int
            The ID of the starboard channel.
        starboard_emoji : str
            The emoji to use for the starboard.
        starboard_threshold : int
            The threshold for the starboard.

        Returns
        -------
        Starboard:
            The created or updated starboard.
        """

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

        Returns
        -------
        Starboard | None:
            The deleted starboard if found and deleted successfully.
            None if no starboard exists for the given guild ID.
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

        Parameters
        ----------
        message_id : int
            The ID of the message.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        StarboardMessage | None:
            The starboard message if found.
            None if no starboard message exists for the given message ID and guild ID.
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
        """
        Create or update a starboard message.

        Parameters
        ----------
        message_id : int
            The ID of the message.
        message_content : str
            The content of the message.
        message_expires_at : datetime
            The expiration date of the message.
        message_channel_id : int
            The ID of the channel the message was sent in.
        message_user_id : int
            The ID of the user who sent the message.
        message_guild_id : int
            The ID of the guild the message was sent in.
        star_count : int
            The number of stars the message has.
        starboard_message_id : int
            The ID of the starboard message.

        Returns
        -------
        StarboardMessage:
            The created or updated starboard message.
        """

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

        Parameters
        ----------
        message_id : int
            The ID of the message.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        StarboardMessage | None:
            The deleted starboard message if found and deleted successfully.
            None if no starboard message exists for the given message ID and guild ID.
        """

        return await self.table.delete(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
        )

    async def get_all_starboard_messages(self, guild_id: int) -> list[StarboardMessage]:
        """
        Get all starboard messages for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        list[StarboardMessage]:
            A list of all starboard messages for the guild.
        """

        return await self.table.find_many(where={"message_guild_id": guild_id})

    async def update_star_count(self, message_id: int, guild_id: int, new_star_count: int) -> StarboardMessage | None:
        """
        Update the star count of a starboard message.

        Parameters
        ----------
        message_id : int
            The ID of the message.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        StarboardMessage | None:
            The updated starboard message if found and updated successfully.
            None if no starboard message exists for the given message ID and guild ID.
        """

        return await self.table.update(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
            data={"star_count": new_star_count},
        )

    async def get_starboard_message_by_id(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """
        Get a starboard message by its ID and guild ID.

        A "starboard message" is the response by the bot, not the original message.

        Parameters
        ----------
        message_id : int
            The ID of the starboard message.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        StarboardMessage | None:
            The starboard message if found.
            None if no starboard message exists for the given starboard message ID and guild ID.
        """
        return await self.table.find_first(where={"message_id": message_id, "message_guild_id": guild_id})
