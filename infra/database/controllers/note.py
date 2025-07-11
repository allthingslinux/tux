from database.client import db
from database.controllers.base import BaseController

from prisma.actions import GuildActions
from prisma.models import Guild, Note


class NoteController(BaseController[Note]):
    """Controller for managing moderator notes.

    This controller provides methods for creating, retrieving, updating,
    and deleting moderator notes for users in guilds.
    """

    def __init__(self):
        """Initialize the NoteController with the note table."""
        super().__init__("note")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_all_notes(self) -> list[Note]:
        """Get all notes across all guilds.

        Returns
        -------
        list[Note]
            List of all notes
        """
        return await self.find_many(where={})

    async def get_note_by_id(self, note_id: int) -> Note | None:
        """Get a note by its ID.

        Parameters
        ----------
        note_id : int
            The ID of the note to get

        Returns
        -------
        Note | None
            The note if found, None otherwise
        """
        return await self.find_unique(where={"note_id": note_id})

    async def insert_note(
        self,
        note_user_id: int,
        note_moderator_id: int,
        note_content: str,
        guild_id: int,
    ) -> Note:
        """Create a new moderator note.

        Parameters
        ----------
        note_user_id : int
            The ID of the user the note is about
        note_moderator_id : int
            The ID of the moderator creating the note
        note_content : str
            The content of the note
        guild_id : int
            The ID of the guild the note belongs to

        Returns
        -------
        Note
            The created note
        """
        return await self.create(
            data={
                "note_user_id": note_user_id,
                "note_moderator_id": note_moderator_id,
                "note_content": note_content,
                "guild": self.connect_or_create_relation("guild_id", guild_id),
            },
            include={"guild": True},
        )

    async def delete_note_by_id(self, note_id: int) -> Note | None:
        """Delete a note by its ID.

        Parameters
        ----------
        note_id : int
            The ID of the note to delete

        Returns
        -------
        Note | None
            The deleted note if found, None otherwise
        """
        return await self.delete(where={"note_id": note_id})

    async def update_note_by_id(self, note_id: int, note_content: str) -> Note | None:
        """Update a note's content.

        Parameters
        ----------
        note_id : int
            The ID of the note to update
        note_content : str
            The new content for the note

        Returns
        -------
        Note | None
            The updated note if found, None otherwise
        """
        return await self.update(
            where={"note_id": note_id},
            data={"note_content": note_content},
        )

    async def get_notes_by_user_id(self, note_user_id: int, limit: int | None = None) -> list[Note]:
        """Get all notes for a user across all guilds.

        Parameters
        ----------
        note_user_id : int
            The ID of the user to get notes for
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes for the user
        """
        return await self.find_many(where={"note_user_id": note_user_id}, take=limit)

    async def get_notes_by_moderator_id(self, moderator_id: int, limit: int | None = None) -> list[Note]:
        """Get all notes created by a moderator across all guilds.

        Parameters
        ----------
        moderator_id : int
            The ID of the moderator to get notes for
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes created by the moderator
        """
        return await self.find_many(where={"note_moderator_id": moderator_id}, take=limit)

    async def get_notes_by_guild_id(self, guild_id: int, limit: int | None = None) -> list[Note]:
        """Get all notes for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get notes for
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes for the guild
        """
        return await self.find_many(where={"guild_id": guild_id}, take=limit)

    async def get_notes_by_user_id_and_guild_id(
        self,
        note_user_id: int,
        guild_id: int,
        limit: int | None = None,
    ) -> list[Note]:
        """Get all notes for a user in a specific guild.

        Parameters
        ----------
        note_user_id : int
            The ID of the user to get notes for
        guild_id : int
            The ID of the guild to get notes from
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes for the user in the guild
        """
        return await self.find_many(where={"note_user_id": note_user_id, "guild_id": guild_id}, take=limit)

    async def get_notes_by_moderator_id_and_guild_id(
        self,
        moderator_id: int,
        guild_id: int,
        limit: int | None = None,
    ) -> list[Note]:
        """Get all notes created by a moderator in a specific guild.

        Parameters
        ----------
        moderator_id : int
            The ID of the moderator to get notes for
        guild_id : int
            The ID of the guild to get notes from
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes created by the moderator in the guild
        """
        return await self.find_many(where={"note_moderator_id": moderator_id, "guild_id": guild_id}, take=limit)

    async def get_notes_by_user_id_and_moderator_id(
        self,
        user_id: int,
        moderator_id: int,
        limit: int | None = None,
    ) -> list[Note]:
        """Get all notes for a user created by a specific moderator.

        Parameters
        ----------
        user_id : int
            The ID of the user to get notes for
        moderator_id : int
            The ID of the moderator who created the notes
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes for the user created by the moderator
        """
        return await self.find_many(where={"note_user_id": user_id, "note_moderator_id": moderator_id}, take=limit)

    async def get_notes_by_user_id_moderator_id_and_guild_id(
        self,
        user_id: int,
        moderator_id: int,
        guild_id: int,
        limit: int | None = None,
    ) -> list[Note]:
        """Get all notes for a user created by a specific moderator in a specific guild.

        Parameters
        ----------
        user_id : int
            The ID of the user to get notes for
        moderator_id : int
            The ID of the moderator who created the notes
        guild_id : int
            The ID of the guild to get notes from
        limit : int | None
            Optional limit on the number of notes to return

        Returns
        -------
        list[Note]
            List of notes for the user created by the moderator in the guild
        """
        return await self.find_many(
            where={
                "note_user_id": user_id,
                "note_moderator_id": moderator_id,
                "guild_id": guild_id,
            },
            take=limit,
        )

    async def count_notes_by_guild_id(self, guild_id: int) -> int:
        """Count the number of notes in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to count notes for

        Returns
        -------
        int
            The number of notes in the guild
        """
        return await self.count(where={"guild_id": guild_id})

    async def count_notes_by_user_id(self, user_id: int, guild_id: int | None = None) -> int:
        """Count the number of notes for a user.

        Parameters
        ----------
        user_id : int
            The ID of the user to count notes for
        guild_id : int | None
            Optional guild ID to restrict the count to

        Returns
        -------
        int
            The number of notes for the user
        """
        where = {"note_user_id": user_id}
        if guild_id is not None:
            where["guild_id"] = guild_id

        return await self.count(where=where)

    async def bulk_delete_notes_by_guild_id(self, guild_id: int) -> int:
        """Delete all notes for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete notes for

        Returns
        -------
        int
            The number of notes deleted
        """
        return await self.delete_many(where={"guild_id": guild_id})
