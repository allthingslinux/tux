from datetime import datetime
from enum import Enum

from prisma.models import Infractions, Notes, Reminders, Snippets, Users
from tux.database.client import db


class InfractionType(Enum):
    BAN = "ban"
    WARN = "warn"
    KICK = "kick"
    TIMEOUT = "timeout"


class UsersController:
    def __init__(self) -> None:
        self.table = db.users

    async def get_all_users(self) -> list[Users]:
        """
        Retrieves all users from the database.

        Returns:
            list[Users]: A list of all users.
        """

        return await self.table.find_many()

    async def get_user_by_id(self, user_id: int) -> Users | None:
        """
        Retrieves a user from the database based on the specified user ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Users | None: The user if found, None if the user does not exist.
        """

        return await self.table.find_first(where={"id": user_id})

    async def create_user(
        self,
        user_id: int,
        name: str,
        display_name: str,
        mention: str,
        bot: bool,
        created_at: datetime,
    ) -> Users:
        """
        Creates a new user in the database with the specified details.

        Args:
            user_id (int): The ID of the user.
            name (str): The name of the user.
            display_name (str): The display name of the user.
            mention (str): The mention tag of the user.
            bot (bool): Indicates if the user is a bot.
            created_at (datetime): The creation date and time of the user.

        Returns:
            Users: The newly created user.
        """

        return await self.table.create(
            data={
                "id": user_id,
                "name": name,
                "display_name": display_name,
                "mention": mention,
                "bot": bot,
                "created_at": created_at,
            }
        )

    async def delete_user(self, user_id: int) -> None:
        """
        Deletes a user from the database based on the specified user ID.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            None
        """

        await self.table.delete(where={"id": user_id})

    async def update_user(
        self,
        user_id: int,
        name: str,
        display_name: str,
        mention: str,
        bot: bool,
        created_at: datetime,
    ) -> Users | None:
        """
        Updates user information in the database with the specified user ID and details.

        Args:
            user_id (int): The ID of the user to update.
            name (str): The name of the user.
            display_name (str): The display name of the user.
            mention (str): The mention tag of the user.
            bot (bool): Indicates if the user is a bot.
            created_at (datetime): The creation date and time of the user.

        Returns:
            Users | None: The updated user if successful, None if the user was not found.
        """

        return await self.table.update(
            where={"id": user_id},
            data={
                "name": name,
                "display_name": display_name,
                "mention": mention,
                "bot": bot,
                "created_at": created_at,
            },
        )

    async def toggle_afk(self, user_id: int, afk: bool) -> Users | None:
        """
        Toggles the AFK status of a user in the database.

        Args:
            user_id (int): The ID of the user to toggle AFK status for.
            afk (bool): The new AFK status to set for the user.

        Returns:
            Users | None: The updated user if successful, None if the user was not found.
        """

        return await self.table.update(
            where={"id": user_id},
            data={"afk": afk},
        )


class InfractionsController:
    def __init__(self) -> None:
        self.table = db.infractions

    async def get_all_infractions(self) -> list[Infractions]:
        """
        Retrieves all infractions from the database.

        Returns:
            list[Infractions]: A list of all infractions.
        """

        return await self.table.find_many()

    async def get_infraction_by_id(self, infraction_id: int) -> Infractions | None:
        """
        Retrieves an infraction from the database based on the specified infraction ID.

        Args:
            infraction_id (int): The ID of the infraction to retrieve.

        Returns:
            Infractions | None: The infraction if found, None if the infraction does not exist.
        """

        return await self.table.find_first(where={"id": infraction_id})

    async def create_infraction(
        self,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
    ) -> Infractions:
        """
        Creates a new infraction in the database with the specified user ID, moderator ID, infraction type, and reason.

        Args:
            user_id (int): The ID of the user for whom the infraction is created.
            moderator_id (int): The ID of the moderator who created the infraction.
            infraction_type (InfractionType): The type of the infraction.
            infraction_reason (str): The reason for the infraction.

        Returns:
            Infractions: The newly created infraction.
        """

        return await self.table.create(
            data={
                "user_id": user_id,
                "moderator_id": moderator_id,
                "infraction_type": infraction_type.value,
                "infraction_reason": infraction_reason,
            }
        )

    async def delete_infraction(self, infraction_id: int) -> None:
        """
        Deletes an infraction from the database based on the specified infraction ID.

        Args:
            infraction_id (int): The ID of the infraction to delete.

        Returns:
            None
        """

        await self.table.delete(where={"id": infraction_id})

    async def update_infraction(
        self, infraction_id: int, infraction_reason: str
    ) -> Infractions | None:
        """
        Updates an infraction in the database with the specified infraction ID and reason.

        Args:
            infraction_id (int): The ID of the infraction to update.
            infraction_reason (str): The new reason for the infraction.

        Returns:
            Infractions | None: The updated infraction if successful, None if the infraction was not found.
        """

        return await self.table.update(
            where={"id": infraction_id},
            data={"infraction_reason": infraction_reason},
        )


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


class SnippetsController:
    def __init__(self) -> None:
        self.table = db.snippets

    async def get_all_snippets(self) -> list[Snippets]:
        """
        Retrieves all snippets from the database.

        Returns:
            list[Snippets]: A list of all snippets.
        """

        return await self.table.find_many()

    async def get_snippet_by_name(self, name: str) -> Snippets | None:
        """
        Retrieves a snippet from the database based on the specified name.

        Args:
            name (str): The name of the snippet to retrieve.

        Returns:
            Snippets | None: The snippet if found, None if the snippet does not exist.
        """

        return await self.table.find_first(where={"name": name})

    async def create_snippet(self, name: str, content: str) -> Snippets:
        """
        Creates a new snippet in the database with the specified name and content.

        Args:
            name (str): The name of the snippet.
            content (str): The content of the snippet.

        Returns:
            Snippets: The newly created snippet.
        """

        return await self.table.create(
            data={
                "name": name,
                "content": content,
            }
        )

    async def delete_snippet(self, name: str) -> None:
        """
        Deletes a snippet from the database based on the specified name.

        Args:
            name (str): The name of the snippet to delete.

        Returns:
            None
        """

        await self.table.delete(where={"name": name})

    async def update_snippet(self, name: str, content: str) -> Snippets | None:
        """
        Updates a snippet in the database with the specified name and content.

        Args:
            name (str): The name of the snippet to update.
            content (str): The new content for the snippet.

        Returns:
            Snippets | None: The updated snippet if successful, None if the snippet was not found.
        """

        return await self.table.update(
            where={"name": name},
            data={"content": content},
        )


class RemindersController:
    def __init__(self) -> None:
        self.table = db.reminders

    async def get_all_reminders(self) -> list[Reminders]:
        """
        Retrieves all reminders from the database.

        Returns:
            list[Reminders]: A list of all reminders.
        """

        return await self.table.find_many()

    async def get_reminder_by_id(self, reminder_id: int) -> Reminders | None:
        """
        Retrieves a reminder from the database based on the specified reminder ID.

        Args:
            reminder_id (int): The ID of the reminder to retrieve.

        Returns:
            Reminders | None: The reminder if found, None if the reminder does not exist.
        """

        return await self.table.find_first(where={"id": reminder_id})

    async def create_reminder(
        self,
        user_id: int,
        reminder_content: str,
        expires_at: datetime,
    ) -> Reminders:
        """
        Creates a new reminder in the database with the specified user ID, reminder content, and expiration date.

        Args:
            user_id (int): The ID of the user for whom the reminder is created.
            reminder_content (str): The content of the reminder.
            expires_at (datetime): The expiration date and time of the reminder.

        Returns:
            Reminders: The newly created reminder.
        """

        return await self.table.create(
            data={
                "user_id": user_id,
                "content": reminder_content,
                "expires_at": expires_at,
            }
        )

    async def delete_reminder(self, reminder_id: int) -> None:
        """
        Deletes a reminder from the database based on the specified reminder ID.

        Args:
            reminder_id (int): The ID of the reminder to delete.

        Returns:
            None
        """

        await self.table.delete(where={"id": reminder_id})

    async def update_reminder(self, reminder_id: int, reminder_content: str) -> Reminders | None:
        """
        Updates a reminder in the database with the specified reminder ID and content.

        Args:
            reminder_id (int): The ID of the reminder to update.
            reminder_content (str): The new content for the reminder.

        Returns:
            Reminders | None: The updated reminder if successful, None if the reminder was not found.
        """

        return await self.table.update(
            where={"id": reminder_id},
            data={"content": reminder_content},
        )


class DatabaseController:
    def __init__(self) -> None:
        self.users = UsersController()
        self.infractions = InfractionsController()
        self.notes = NotesController()
        self.snippets = SnippetsController()
        self.reminders = RemindersController()


db_controller = DatabaseController()
