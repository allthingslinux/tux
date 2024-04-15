from prisma.models import UserRoles
from tux.database.client import db


class UserRolesController:
    def __init__(self) -> None:
        self.table = db.userroles

    async def get_all_user_roles(self) -> list[UserRoles]:
        """
        Retrieves all user roles from the database.

        Returns:
            list[UserRoles]: A list of all user roles.
        """

        return await self.table.find_many()

    async def get_user_role_by_ids(self, user_id: int, role_id: int) -> UserRoles | None:
        """
        Retrieves a user role from the database based on the specified user ID and role ID.
        Args:
            user_id (int): The ID of the user.
            role_id (int): The ID of the role.
        Returns:
            UserRoles | None: The user role if found, None if the user role does not exist.
        """
        return await self.table.find_first(where={"user_id": user_id, "role_id": role_id})

    async def create_user_role(self, user_id: int, role_id: int) -> UserRoles:
        """
        Creates a new user role with the specified user ID and role ID.
        Args:
            user_id (int), role_id (int)
        Returns:
            UserRoles: The newly created user role.
        """
        return await self.table.create(data={"user_id": user_id, "role_id": role_id})

    async def delete_user_role(self, user_id: int, role_id: int) -> None:
        """
        Deletes a user role based on specified user ID and role ID.
        """
        await self.table.delete(where={"user_id_role_id": {"user_id": user_id, "role_id": role_id}})

    async def delete_user_roles(self, user_id: int) -> None:
        """
        Deletes all user roles from the database based on the specified user ID.
        """
        await self.table.delete_many(where={"user_id": user_id})

    async def delete_role_users(self, role_id: int) -> None:
        """
        Deletes all user roles from the database based on the specified role ID.
        """
        await self.table.delete_many(where={"role_id": role_id})

    async def delete_all_user_roles(self) -> None:
        """
        Deletes all user roles from the database.
        """
        await self.table.delete_many()

    async def get_user_roles_by_user_id(self, user_id: int) -> list[UserRoles]:
        """
        Retrieves all user roles from the database based on the specified user ID.
        """
        return await self.table.find_many(where={"user_id": user_id})

    async def get_user_roles_by_role_id(self, role_id: int) -> list[UserRoles]:
        """
        Retrieves all user roles from the database based on the specified role ID.
        """
        return await self.table.find_many(where={"role_id": role_id})

    async def sync_user_roles(self, user_id: int, role_ids: list[int]) -> None:
        """
        Synchronizes user roles in the database based on the specified user ID and role IDs.
        """
        user_roles = await self.get_user_roles_by_user_id(user_id)
        user_role_ids = [user_role.role_id for user_role in user_roles]

        for role_id in role_ids:
            if role_id not in user_role_ids:
                await self.create_user_role(user_id=user_id, role_id=role_id)

        for user_role in user_roles:
            if user_role.role_id not in role_ids:
                await self.delete_user_role(user_id=user_id, role_id=user_role.role_id)
