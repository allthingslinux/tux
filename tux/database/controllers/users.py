from datetime import datetime

from prisma.models import Users
from prisma.types import UsersUpdateInput
from tux.database.client import db


class UsersController:
    def __init__(self) -> None:
        """
        Initializes the controller and connects to the users table in the database.
        """
        self.table = db.users

    async def get_all_users(self) -> list[Users]:
        """
        Retrieves all users from the database.

        Returns
        -------
        list[Users]
            A list of all users.
        """
        return await self.table.find_many()

    async def get_user_by_id(self, user_id: int) -> Users | None:
        """
        Retrieves a user from the database based on the specified user ID.

        Parameters
        ----------
        user_id : int
            The ID of the user to retrieve.

        Returns
        -------
        Users or None
            The user if found, otherwise None.
        """
        return await self.table.find_first(where={"id": user_id})

    async def create_user(
        self,
        user_id: int,
        name: str,
        display_name: str,
        mention: str,
        bot: bool,
        created_at: datetime | None,
        joined_at: datetime | None,
    ) -> Users:
        """
        Creates a new user in the database with the specified details.

        Parameters
        ----------
        user_id : int
            The unique identifier for the user.
        name : str
            The name of the user.
        display_name : str
            The display name of the user.
        mention : str
            The mention tag of the user.
        bot : bool
            Whether the user is a bot.
        created_at : datetime or None
            The creation date of the user account.
        joined_at : datetime or None
            The date the user joined, which could be None.

        Returns
        -------
        Users
            The newly created user record.
        """
        return await self.table.create(
            data={
                "id": user_id,
                "name": name,
                "display_name": display_name,
                "mention": mention,
                "bot": bot,
                "created_at": created_at,
                "joined_at": joined_at,
            }
        )

    async def update_user(
        self,
        user_id: int,
        name: str | None = None,
        display_name: str | None = None,
        mention: str | None = None,
        bot: bool | None = None,
        created_at: datetime | None = None,
        joined_at: datetime | None = None,
    ) -> Users | None:
        """
        Updates user information in the database based on the specified user ID and details.

        Parameters
        ----------
        user_id : int
            The user ID for the update.
        name : str or None, optional
            The new name of the user.
        display_name : str or None, optional
            The new display name of the user.
        mention : str or None, optional
            The new mention tag of the user.
        bot : bool or None, optional
            Whether the user is a bot.
        created_at : datetime or None, optional
            The creation date to set.
        joined_at : datetime or None, optional
            The join date to set.

        Returns
        -------
        Users or None
            The updated user record if successful, otherwise None.
        """
        data: UsersUpdateInput = {}

        if name is not None:
            data["name"] = name
        if display_name is not None:
            data["display_name"] = display_name
        if mention is not None:
            data["mention"] = mention
        if bot is not None:
            data["bot"] = bot
        if created_at is not None:
            data["created_at"] = created_at
        if joined_at is not None:
            data["joined_at"] = joined_at

        return await self.table.update(where={"id": user_id}, data=data)

    async def sync_user(
        self,
        user_id: int,
        name: str,
        display_name: str,
        mention: str,
        bot: bool,
        created_at: datetime,
        joined_at: datetime | None,
    ) -> Users | None:
        """
        Synchronizes a user in the database based on the specified user ID and details.

        Parameters
        ----------
        user_id : int
            The user ID to synchronize.
        name : str
            The name of the user.
        display_name : str
            The display name of the user.
        mention : str
            The mention tag of the user.
        bot : bool
            Whether the user is a bot.
        created_at : datetime
            The creation date of the user account.
        joined_at : datetime or None
            The date the user joined, which could be None.

        Returns
        -------
        Users or None
            The updated user record if successful, otherwise None.
        """

        existing_user = await self.get_user_by_id(user_id)

        if existing_user is None:
            return await self.create_user(
                user_id=user_id,
                name=name,
                display_name=display_name,
                mention=mention,
                bot=bot,
                created_at=created_at,
                joined_at=joined_at,
            )

        if (
            existing_user.name != name
            or existing_user.display_name != display_name
            or existing_user.mention != mention
            or existing_user.bot != bot
            or existing_user.created_at != created_at
            or existing_user.joined_at != joined_at
        ):
            return await self.update_user(
                user_id=user_id,
                name=name if existing_user.name != name else None,
                display_name=display_name if existing_user.display_name != display_name else None,
                mention=mention if existing_user.mention != mention else None,
                bot=bot if existing_user.bot != bot else None,
                created_at=created_at if existing_user.created_at != created_at else None,
                joined_at=joined_at if existing_user.joined_at != joined_at else None,
            )

        return existing_user

    async def delete_user(self, user_id: int) -> None:
        """
        Deletes a user from the database based on the specified user ID.

        Parameters
        ----------
        user_id : int
            The user ID of the user to delete.

        Returns
        -------
        None
        """
        await self.table.delete(where={"id": user_id})

    async def toggle_afk(self, user_id: int, afk: bool) -> Users | None:
        """
        Toggles the AFK status of a user in the database.

        Parameters
        ----------
        user_id : int
            The ID of the user to toggle AFK status for.
        afk : bool
            The new AFK status to set for the user.

        Returns
        -------
        Users or None
            The updated user if successful, None if the user was not found.
        """
        return await self.table.update(
            where={"id": user_id},
            data={"afk": afk},
        )
