from __future__ import annotations

from typing import Any

from tux.database.controllers.base import BaseController
from tux.database.models import Starboard, StarboardMessage
from tux.database.service import DatabaseService


class StarboardController(BaseController[Starboard]):
    """Clean Starboard controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(Starboard, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_starboard_by_guild(self, guild_id: int) -> Starboard | None:
        """Get starboard configuration for a guild."""
        return await self.find_one(filters=Starboard.guild_id == guild_id)

    async def get_or_create_starboard(self, guild_id: int, **defaults: Any) -> Starboard:
        """Get starboard configuration, or create it with defaults if it doesn't exist."""
        starboard = await self.get_starboard_by_guild(guild_id)
        if starboard is not None:
            return starboard
        return await self.create(guild_id=guild_id, **defaults)

    async def update_starboard(self, guild_id: int, **updates: Any) -> Starboard | None:
        """Update starboard configuration."""
        starboard = await self.get_starboard_by_guild(guild_id)
        if starboard is None:
            return None
        return await self.update_by_id(guild_id, **updates)

    async def delete_starboard(self, guild_id: int) -> bool:
        """Delete starboard configuration for a guild."""
        starboard = await self.get_starboard_by_guild(guild_id)
        return False if starboard is None else await self.delete_by_id(guild_id)

    async def get_all_starboards(self) -> list[Starboard]:
        """Get all starboard configurations."""
        return await self.find_all()

    async def get_starboard_count(self) -> int:
        """Get the total number of starboard configurations."""
        return await self.count()

    # Additional methods that module files expect
    async def create_or_update_starboard(self, guild_id: int, **kwargs: Any) -> Starboard:
        """Create or update starboard configuration for a guild."""
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
        """Delete starboard configuration for a guild."""
        return await self.delete_starboard(guild_id)

    async def get_starboard_by_guild_id(self, guild_id: int) -> Starboard | None:
        """Get starboard configuration by guild ID - alias for get_starboard_by_guild."""
        return await self.get_starboard_by_guild(guild_id)


class StarboardMessageController(BaseController[StarboardMessage]):
    """Clean StarboardMessage controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(StarboardMessage, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_message_by_id(self, message_id: int) -> StarboardMessage | None:
        """Get a starboard message by its ID."""
        return await self.get_by_id(message_id)

    async def get_message_by_original(self, original_message_id: int, guild_id: int) -> StarboardMessage | None:
        """Get a starboard message by its original message ID and guild."""
        return await self.find_one(
            filters=(StarboardMessage.message_id == original_message_id)
            & (StarboardMessage.message_guild_id == guild_id),
        )

    async def get_messages_by_guild(self, guild_id: int, limit: int | None = None) -> list[StarboardMessage]:
        """Get all starboard messages in a guild."""
        messages = await self.find_all(filters=StarboardMessage.message_guild_id == guild_id)
        # Sort by star count descending and limit
        sorted_messages = sorted(messages, key=lambda x: x.star_count, reverse=True)
        return sorted_messages[:limit] if limit else sorted_messages

    async def create_starboard_message(
        self,
        original_message_id: int,
        starboard_message_id: int,
        guild_id: int,
        channel_id: int,
        star_count: int = 1,
        **kwargs: Any,
    ) -> StarboardMessage:
        """Create a new starboard message."""
        return await self.create(
            message_id=original_message_id,
            starboard_message_id=starboard_message_id,
            message_guild_id=guild_id,
            message_channel_id=channel_id,
            star_count=star_count,
            **kwargs,
        )

    async def update_star_count(self, message_id: int, new_star_count: int) -> StarboardMessage | None:
        """Update the star count for a starboard message."""
        return await self.update_by_id(message_id, star_count=new_star_count)

    async def delete_starboard_message(self, message_id: int) -> bool:
        """Delete a starboard message."""
        return await self.delete_by_id(message_id)

    async def get_top_messages(self, guild_id: int, limit: int = 10) -> list[StarboardMessage]:
        """Get top starboard messages by star count in a guild."""
        messages = await self.find_all(filters=StarboardMessage.message_guild_id == guild_id)
        # Sort by star count descending and limit
        sorted_messages = sorted(messages, key=lambda x: x.star_count, reverse=True)
        return sorted_messages[:limit]

    async def get_message_count_by_guild(self, guild_id: int) -> int:
        """Get the total number of starboard messages in a guild."""
        return await self.count(filters=StarboardMessage.message_guild_id == guild_id)

    async def get_messages_by_channel(self, channel_id: int) -> list[StarboardMessage]:
        """Get all starboard messages in a specific channel."""
        return await self.find_all(filters=StarboardMessage.message_channel_id == channel_id)

    # Additional methods that module files expect
    async def get_starboard_message_by_id(self, message_id: int) -> StarboardMessage | None:
        """Get a starboard message by its ID."""
        return await self.get_message_by_id(message_id)

    async def create_or_update_starboard_message(self, **kwargs: Any) -> StarboardMessage:
        """Create or update a starboard message."""
        # Check if message already exists
        if "message_id" in kwargs and "message_guild_id" in kwargs:
            existing = await self.get_message_by_original(kwargs["message_id"], kwargs["message_guild_id"])
            if existing:
                # Update existing
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                updated = await self.update_by_id(existing.message_id, **kwargs)
                return updated if updated is not None else existing

        # Create new
        return await self.create(**kwargs)
