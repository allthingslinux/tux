from datetime import datetime

from prisma.models import Users

# from prisma.types import UsersCreateWithoutRelationsInput
from tux.database.client import db


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
        created_at: datetime | None,
        joined_at: datetime | None,
    ) -> Users:
        """Creates a new user in the database with the specified details."""

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

    # TODO: Implement bulk_create_users

    # async def bulk_create_users(
    #     self, users: list[UsersCreateWithoutRelationsInput] | None
    # ) -> int | None:
    #     """Creates multiple users in the database with the specified details."""
    #     return await self.table.create_many(data=users or [])

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
        """Updates user information in the database with the specified user ID and details."""

        return await self.table.update(
            where={"id": user_id},
            data={
                "name": name or "",
                "display_name": display_name or "",
                "mention": mention or "",
                "bot": bot or False,
                "created_at": created_at or None,
                "joined_at": joined_at or None,
            },
        )

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
        """Deletes a user from the database based on the specified user ID."""

        await self.table.delete(where={"id": user_id})

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
