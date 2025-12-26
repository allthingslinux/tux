"""
Starboard message highlighting controller.

This controller manages starboard functionality for Discord guilds, allowing
popular messages to be automatically posted to designated starboard channels
based on reaction thresholds and user preferences.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tux.database.controllers.base import BaseController
from tux.database.models import Starboard, StarboardMessage

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class StarboardController(BaseController[Starboard]):
    """Clean Starboard controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the starboard controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Starboard, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_starboard_by_guild(self, guild_id: int) -> Starboard | None:
        """
        Get starboard configuration for a guild.

        Returns
        -------
        Starboard | None
            The starboard configuration if found, None otherwise.
        """
        return await self.find_one(filters=Starboard.id == guild_id)

    async def get_or_create_starboard(
        self,
        guild_id: int,
        **defaults: Any,
    ) -> Starboard:
        """
        Get starboard configuration, or create it with defaults if it doesn't exist.

        Returns
        -------
        Starboard
            The starboard configuration (existing or newly created).
        """
        starboard = await self.get_starboard_by_guild(guild_id)
        if starboard is not None:
            return starboard
        return await self.create(guild_id=guild_id, **defaults)

    async def update_starboard(self, guild_id: int, **updates: Any) -> Starboard | None:
        """
        Update starboard configuration.

        Returns
        -------
        Starboard | None
            The updated starboard configuration, or None if not found.
        """
        starboard = await self.get_starboard_by_guild(guild_id)
        if starboard is None:
            return None
        return await self.update_by_id(guild_id, **updates)

    async def delete_starboard(self, guild_id: int) -> bool:
        """
        Delete starboard configuration for a guild.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        starboard = await self.get_starboard_by_guild(guild_id)
        return False if starboard is None else await self.delete_by_id(guild_id)

    async def get_all_starboards(self) -> list[Starboard]:
        """
        Get all starboard configurations.

        Returns
        -------
        list[Starboard]
            List of all starboard configurations.
        """
        return await self.find_all()

    async def get_starboard_count(self) -> int:
        """
        Get the total number of starboard configurations.

        Returns
        -------
        int
            The total count of starboard configurations.
        """
        return await self.count()

    # Additional methods that module files expect
    async def create_or_update_starboard(
        self,
        guild_id: int,
        **kwargs: Any,
    ) -> Starboard:
        """
        Create or update starboard configuration for a guild.

        Returns
        -------
        Starboard
            The starboard configuration (created or updated).
        """
        existing = await self.get_starboard_by_guild(guild_id)
        if existing:
            # Update existing
            for key, value in kwargs.items():
                setattr(existing, key, value)
            updated = await self.update_by_id(guild_id, **kwargs)
            return updated if updated is not None else existing
        # Create new
        return await self.create(guild_id=guild_id, **kwargs)

    async def delete_starboard_by_guild_id(self, guild_id: int) -> bool:
        """
        Delete starboard configuration for a guild.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_starboard(guild_id)

    async def get_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        """
        Get starboard configuration by guild ID - alias for get_starboard_by_guild.

        Returns
        -------
        Starboard | None
            The starboard configuration if found, None otherwise.
        """
        return await self.get_starboard_by_guild(guild_id)


class StarboardMessageController(BaseController[StarboardMessage]):
    """Clean StarboardMessage controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the starboard message controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(StarboardMessage, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_message_by_id(self, message_id: int) -> StarboardMessage | None:
        """
        Get a starboard message by its ID.

        Returns
        -------
        StarboardMessage | None
            The starboard message if found, None otherwise.
        """
        return await self.get_by_id(message_id)

    async def get_message_by_original(
        self,
        original_message_id: int,
        guild_id: int,
    ) -> StarboardMessage | None:
        """
        Get a starboard message by its original message ID and guild.

        Returns
        -------
        StarboardMessage | None
            The starboard message if found, None otherwise.
        """
        return await self.find_one(
            filters=(StarboardMessage.id == original_message_id)
            & (StarboardMessage.message_guild_id == guild_id),
        )

    async def get_messages_by_guild(
        self,
        guild_id: int,
        limit: int | None = None,
    ) -> list[StarboardMessage]:
        """
        Get all starboard messages in a guild.

        Returns
        -------
        list[StarboardMessage]
            List of starboard messages sorted by star count (limited if specified).
        """
        # Use database-level sorting and limiting for better performance
        return await self.find_all(
            filters=StarboardMessage.message_guild_id == guild_id,
            order_by=[StarboardMessage.star_count.desc()],  # type: ignore[attr-defined]
            limit=limit,
        )

    async def create_starboard_message(
        self,
        original_message_id: int,
        starboard_message_id: int,
        guild_id: int,
        channel_id: int,
        star_count: int = 1,
        **kwargs: Any,
    ) -> StarboardMessage:
        """
        Create a new starboard message.

        Returns
        -------
        StarboardMessage
            The newly created starboard message.
        """
        return await self.create(
            id=original_message_id,
            starboard_message_id=starboard_message_id,
            message_guild_id=guild_id,
            message_channel_id=channel_id,
            star_count=star_count,
            **kwargs,
        )

    async def update_star_count(
        self,
        message_id: int,
        new_star_count: int,
    ) -> StarboardMessage | None:
        """
        Update the star count for a starboard message.

        Returns
        -------
        StarboardMessage | None
            The updated starboard message, or None if not found.
        """
        return await self.update_by_id(message_id, star_count=new_star_count)

    async def delete_starboard_message(self, message_id: int) -> bool:
        """
        Delete a starboard message.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(message_id)

    async def get_top_messages(
        self,
        guild_id: int,
        limit: int = 10,
    ) -> list[StarboardMessage]:
        """
        Get top starboard messages by star count in a guild.

        Returns
        -------
        list[StarboardMessage]
            List of top starboard messages sorted by star count.
        """
        # Use database-level sorting and limiting for better performance
        return await self.find_all(
            filters=StarboardMessage.message_guild_id == guild_id,
            order_by=[StarboardMessage.star_count.desc()],  # type: ignore[attr-defined]
            limit=limit,
        )

    async def get_message_count_by_guild(self, guild_id: int) -> int:
        """
        Get the total number of starboard messages in a guild.

        Returns
        -------
        int
            The total count of starboard messages in the guild.
        """
        return await self.count(filters=StarboardMessage.message_guild_id == guild_id)

    async def get_messages_by_channel(self, channel_id: int) -> list[StarboardMessage]:
        """
        Get all starboard messages in a specific channel.

        Returns
        -------
        list[StarboardMessage]
            List of all starboard messages in the channel.
        """
        return await self.find_all(
            filters=StarboardMessage.message_channel_id == channel_id,
        )

    # Additional methods that module files expect
    async def get_starboard_message_by_id(
        self,
        message_id: int,
    ) -> StarboardMessage | None:
        """
        Get a starboard message by its ID.

        Returns
        -------
        StarboardMessage | None
            The starboard message if found, None otherwise.
        """
        return await self.get_message_by_id(message_id)

    async def create_or_update_starboard_message(
        self,
        **kwargs: Any,
    ) -> StarboardMessage:
        """
        Create or update a starboard message.

        Returns
        -------
        StarboardMessage
            The starboard message (created or updated).
        """
        # Check if message already exists
        if "id" in kwargs and "message_guild_id" in kwargs:
            existing = await self.get_message_by_original(
                kwargs["id"],
                kwargs["message_guild_id"],
            )
            if existing:
                # Update existing
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                updated = await self.update_by_id(existing.id, **kwargs)
                return updated if updated is not None else existing

        # Create new
        return await self.create(**kwargs)
