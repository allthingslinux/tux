from prisma.models import EmojiStats
from tux.database.client import db


class EmojiStatsController:
    def __init__(self) -> None:
        self.table = db.emojistats

    async def get_all_emoji_stats(self) -> list[EmojiStats]:
        """
        Retrieves all emoji stats from the database.

        Returns:
            list[EmojiStats]: A list of all emoji stats.
        """

        return await self.table.find_many()

    async def get_emoji_stats(self, emoji_id: int) -> EmojiStats | None:
        """
        Retrieves emoji stats from the database based on the specified emoji ID.

        Args:
            emoji_id (int): The ID of the emoji to retrieve.

        Returns:
            EmojiStats | None: The emoji stats if found, None if the emoji does not exist.
        """

        return await self.table.find_first(where={"emoji_id": emoji_id})

    async def create_emoji_stats(self, emoji_id: int, count: int) -> EmojiStats:
        """
        Creates a new emoji stats in the database with the specified emoji ID and count.

        Args:
            emoji_id (int): The ID of the emoji for which the stats are created.
            count (int | None): The count of the emoji.

        Returns:
            EmojiStats: The newly created emoji stats.
        """

        return await self.table.create(
            data={
                "emoji_id": emoji_id,
                "count": count,
            }
        )

    async def increment_emoji_count_or_create(self, emoji_id: int) -> EmojiStats | None:
        """
        Increments the count of the specified emoji in the database or creates a new entry if the emoji does not exist.

        Args:
            emoji_id (int): The ID of the emoji to increment.

        Returns:
            EmojiStats: The updated or newly created emoji stats.
        """

        emoji_stats = await self.get_emoji_stats(emoji_id)

        if emoji_stats is None:
            return await self.create_emoji_stats(emoji_id, 1)

        return await self.update_emoji_count(emoji_id, emoji_stats.count + 1)

    async def update_emoji_count(self, emoji_id: int, count: int) -> EmojiStats | None:
        """
        Updates the count of the specified emoji in the database.

        Args:
            emoji_id (int): The ID of the emoji to update.
            count (int): The new count of the emoji.

        Returns:
            EmojiStats | None: The updated emoji stats if successful, None otherwise.
        """

        return await self.table.update(
            where={"emoji_id": emoji_id},
            data={"count": count},
        )
