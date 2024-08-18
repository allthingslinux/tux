from prisma.enums import SuggestionStatus
from prisma.models import Guild, Suggestion
from tux.database.client import db


class SuggestionController:
    def __init__(self) -> None:
        self.table = db.suggestion
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild:
        """
        Ensure a guild exists in the database and return the found or created object.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to ensure exists.

        Returns
        -------
        Guild
            The guild database object.
        """
        guild = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def create_suggestion(
        self,
        suggestion_title: str,
        suggestion_description: str,
        suggestion_status: SuggestionStatus,
        suggestion_user_id: int,
        guild_id: int,
    ) -> Suggestion:
        await self.ensure_guild_exists(guild_id)

        return await self.table.create(
            data={
                "suggestion_title": suggestion_title,
                "suggestion_description": suggestion_description,
                "suggestion_status": suggestion_status,
                "suggestion_user_id": suggestion_user_id,
                "guild_id": guild_id,
            },
        )
