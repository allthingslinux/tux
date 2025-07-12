from datetime import datetime

from database.client import db
from database.controllers.base import BaseController

from prisma.actions import GuildActions
from prisma.models import Guild, Starboard, StarboardMessage


class StarboardController(BaseController[Starboard]):
    """Controller for managing starboards.

    This controller provides methods for creating, retrieving, updating,
    and deleting starboards for guilds.
    """

    def __init__(self):
        """Initialize the StarboardController with the starboard table."""
        super().__init__("starboard")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_all_starboards(self) -> list[Starboard]:
        """Get all starboards.

        Returns
        -------
        list[Starboard]
            A list of all starboards
        """
        return await self.find_many(where={})

    async def get_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        """Get a starboard by guild ID.

        Parameters
        ----------
        guild_id : int
            The ID of the guild

        Returns
        -------
        Starboard | None
            The starboard if found, None otherwise
        """
        return await self.find_unique(where={"guild_id": guild_id})

    async def create_or_update_starboard(
        self,
        guild_id: int,
        starboard_channel_id: int,
        starboard_emoji: str,
        starboard_threshold: int,
    ) -> Starboard:
        """Create or update a starboard.

        Parameters
        ----------
        guild_id : int
            The ID of the guild
        starboard_channel_id : int
            The ID of the starboard channel
        starboard_emoji : str
            The emoji to use for the starboard
        starboard_threshold : int
            The threshold for the starboard

        Returns
        -------
        Starboard
            The created or updated starboard
        """
        return await self.upsert(
            where={"guild_id": guild_id},
            create={
                "starboard_channel_id": starboard_channel_id,
                "starboard_emoji": starboard_emoji,
                "starboard_threshold": starboard_threshold,
                "guild_id": guild_id,
            },
            update={
                "starboard_channel_id": starboard_channel_id,
                "starboard_emoji": starboard_emoji,
                "starboard_threshold": starboard_threshold,
            },
        )

    async def delete_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        """Delete a starboard by guild ID.

        Parameters
        ----------
        guild_id : int
            The ID of the guild

        Returns
        -------
        Starboard | None
            The deleted starboard if found, None otherwise
        """
        return await self.delete(where={"guild_id": guild_id})

    async def count_starboards(self) -> int:
        """Count all starboards.

        Returns
        -------
        int
            The number of starboards
        """
        return await self.count(where={})


class StarboardMessageController(BaseController[StarboardMessage]):
    """Controller for managing starboard messages.

    This controller provides methods for creating, retrieving, updating,
    and deleting starboard messages.
    """

    def __init__(self):
        """Initialize the StarboardMessageController with the starboardmessage table."""
        super().__init__("starboardmessage")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_starboard_message(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """Get a starboard message by message ID and guild ID.

        Parameters
        ----------
        message_id : int
            The ID of the message
        guild_id : int
            The ID of the guild

        Returns
        -------
        StarboardMessage | None
            The starboard message if found, None otherwise
        """
        return await self.find_unique(
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
        """Create or update a starboard message.

        Parameters
        ----------
        message_id : int
            The ID of the message
        message_content : str
            The content of the message
        message_expires_at : datetime
            The expiration date of the message
        message_channel_id : int
            The ID of the channel the message was sent in
        message_user_id : int
            The ID of the user who sent the message
        message_guild_id : int
            The ID of the guild the message was sent in
        star_count : int
            The number of stars the message has
        starboard_message_id : int
            The ID of the starboard message

        Returns
        -------
        StarboardMessage
            The created or updated starboard message
        """

        # Use transaction to ensure atomicity of guild creation and message upsert
        async def create_or_update_tx():
            # Ensure guild exists through connect_or_create in the upsert
            return await self.upsert(
                where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": message_guild_id}},
                create={
                    "message_id": message_id,
                    "message_content": message_content,
                    "message_expires_at": message_expires_at,
                    "message_channel_id": message_channel_id,
                    "message_user_id": message_user_id,
                    "message_guild_id": message_guild_id,
                    "star_count": star_count,
                    "starboard_message_id": starboard_message_id,
                },
                update={
                    "message_content": message_content,
                    "message_expires_at": message_expires_at,
                    "message_channel_id": message_channel_id,
                    "message_user_id": message_user_id,
                    "star_count": star_count,
                    "starboard_message_id": starboard_message_id,
                },
            )

        return await self.execute_transaction(create_or_update_tx)

    async def delete_starboard_message(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """Delete a starboard message by message ID and guild ID.

        Parameters
        ----------
        message_id : int
            The ID of the message
        guild_id : int
            The ID of the guild

        Returns
        -------
        StarboardMessage | None
            The deleted starboard message if found, None otherwise
        """
        return await self.delete(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
        )

    async def get_all_starboard_messages(
        self,
        guild_id: int,
        limit: int | None = None,
        order_by_stars: bool = False,
    ) -> list[StarboardMessage]:
        """Get all starboard messages for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild
        limit : int | None
            Optional limit on the number of messages to return
        order_by_stars : bool
            Whether to order by star count (highest first)

        Returns
        -------
        list[StarboardMessage]
            A list of all starboard messages for the guild
        """
        order = {"star_count": "desc"} if order_by_stars else {"message_expires_at": "desc"}

        return await self.find_many(
            where={"message_guild_id": guild_id},
            order=order,
            take=limit,
        )

    async def update_star_count(self, message_id: int, guild_id: int, new_star_count: int) -> StarboardMessage | None:
        """Update the star count of a starboard message.

        Parameters
        ----------
        message_id : int
            The ID of the message
        guild_id : int
            The ID of the guild
        new_star_count : int
            The new star count

        Returns
        -------
        StarboardMessage | None
            The updated starboard message if found, None otherwise
        """
        return await self.update(
            where={"message_id_message_guild_id": {"message_id": message_id, "message_guild_id": guild_id}},
            data={"star_count": new_star_count},
        )

    async def get_starboard_message_by_id(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """Get a starboard message by its ID and guild ID.

        A "starboard message" is the response by the bot, not the original message.

        Parameters
        ----------
        message_id : int
            The ID of the starboard message
        guild_id : int
            The ID of the guild

        Returns
        -------
        StarboardMessage | None
            The starboard message if found, None otherwise
        """
        return await self.find_one(where={"message_id": message_id, "message_guild_id": guild_id})

    async def increment_star_count(self, message_id: int, guild_id: int) -> StarboardMessage | None:
        """Increment the star count of a starboard message.

        This method uses a transaction to ensure atomicity.

        Parameters
        ----------
        message_id : int
            The ID of the message
        guild_id : int
            The ID of the guild

        Returns
        -------
        StarboardMessage | None
            The updated starboard message if found, None otherwise
        """

        async def increment_tx():
            message = await self.get_starboard_message(message_id, guild_id)
            if message is None:
                return None

            star_count = self.safe_get_attr(message, "star_count", 0)
            return await self.update_star_count(message_id, guild_id, star_count + 1)

        return await self.execute_transaction(increment_tx)

    async def get_top_starred_messages(self, guild_id: int, limit: int = 10) -> list[StarboardMessage]:
        """Get the top starred messages for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild
        limit : int
            The maximum number of messages to return

        Returns
        -------
        list[StarboardMessage]
            The top starred messages
        """
        return await self.find_many(
            where={"message_guild_id": guild_id},
            order={"star_count": "desc"},
            take=limit,
        )

    async def count_starboard_messages(self, guild_id: int) -> int:
        """Count the number of starboard messages for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild

        Returns
        -------
        int
            The number of starboard messages
        """
        return await self.count(where={"message_guild_id": guild_id})

    async def bulk_delete_messages_by_guild_id(self, guild_id: int) -> int:
        """Delete all starboard messages for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild

        Returns
        -------
        int
            The number of messages deleted
        """
        return await self.delete_many(where={"message_guild_id": guild_id})

    async def get_messages_for_user(
        self,
        user_id: int,
        guild_id: int | None = None,
        limit: int | None = None,
    ) -> list[StarboardMessage]:
        """Get all starboard messages for a user.

        Parameters
        ----------
        user_id : int
            The ID of the user
        guild_id : int | None
            Optional guild ID to filter by
        limit : int | None
            Optional limit on the number of messages to return

        Returns
        -------
        list[StarboardMessage]
            The starboard messages for the user
        """
        where = {"message_user_id": user_id}
        if guild_id is not None:
            where["message_guild_id"] = guild_id

        return await self.find_many(
            where=where,
            order={"star_count": "desc"},
            take=limit,
        )
