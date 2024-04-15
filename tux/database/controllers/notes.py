from prisma.models import Notes
from tux.database.client import db


class NotesController:
    def __init__(self) -> None:
        self.table = db.notes

    async def get_all_notes(self) -> list[Notes]:
        """
        Retrieves all notes from the database.

        Returns:
            list[Notes]: A list of all notes.
        """

        return await self.table.find_many()

    async def get_note_by_id(self, note_id: int) -> Notes | None:
        """
        Retrieves a note from the database based on the specified note ID.

        Args:
            note_id (int): The ID of the note to retrieve.

        Returns:
            Notes | None: The note if found, None if the note does not exist.
        """

        return await self.table.find_first(where={"id": note_id})

    async def create_note(
        self,
        user_id: int,
        moderator_id: int,
        note_content: str,
    ) -> Notes:
        """
        Creates a new note in the database with the specified user ID, moderator ID, and content.

        Args:
            user_id (int): The ID of the user for whom the note is created.
            moderator_id (int): The ID of the moderator who created the note.
            note_content (str): The content of the note.

        Returns:
            Notes: The newly created note.
        """

        return await self.table.create(
            data={
                "user_id": user_id,
                "moderator_id": moderator_id,
                "content": note_content,
            }
        )

    async def delete_note(self, note_id: int) -> None:
        """
        Deletes a note from the database based on the specified note ID.

        Args:
            note_id (int): The ID of the note to delete.

        Returns:
            None
        """

        await self.table.delete(where={"id": note_id})

    async def update_note(self, note_id: int, note_content: str) -> Notes | None:
        """
        Updates a note in the database with the specified note ID and content.

        Args:
            note_id (int): The ID of the note to update.
            note_content (str): The new content for the note.

        Returns:
            Notes | None: The updated note if successful, None if the note was not found.
        """

        return await self.table.update(
            where={"id": note_id},
            data={"content": note_content},
        )
