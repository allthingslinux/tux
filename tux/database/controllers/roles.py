from datetime import datetime

from prisma.models import Roles
from tux.database.client import db


class RolesController:
    def __init__(self) -> None:
        self.table = db.roles

    async def get_all_roles(self) -> list[Roles]:
        """
        Retrieves all roles from the database.

        Returns:
            list[Roles]: A list of all roles.
        """

        return await self.table.find_many()

    async def get_role_by_id(self, role_id: int) -> Roles | None:
        """
        Retrieves a role from the database based on the specified role ID.

        Args:
            role_id (int): The ID of the role to retrieve.

        Returns:
            Roles | None: The role if found, None if the role does not exist.
        """

        return await self.table.find_first(where={"id": role_id})

    async def create_role(
        self,
        role_id: int,
        role_name: str,
        hoist: bool = False,
        managed: bool = False,
        mentionable: bool = False,
        created_at: datetime | None = None,
        mention: str | None = None,
        color: int | None = None,
    ) -> Roles:
        """
        Creates a new role in the database with the specified name and permissions.

        Args:
            role_name (str): The name of the role.
            role_permissions (int): The permissions of the role.

        Returns:
            Roles: The newly created role.
        """

        return await self.table.create(
            data={
                "id": role_id,
                "name": role_name,
                "hoist": hoist,
                "managed": managed,
                "mentionable": mentionable,
                "created_at": created_at,
                "mention": mention,
                "color": color,
            }
        )

    async def update_role(
        self,
        role_id: int,
        role_name: str | None = None,
        hoist: bool | None = None,
        managed: bool | None = None,
        mentionable: bool | None = None,
        mention: str | None = None,
        color: int | None = None,
    ) -> Roles | None:
        """
        Updates a role in the database based on the specified role ID.

        Args:
            role_id (int): The ID of the role to update.
            role_name (str | None): The new name of the role.
            hoist (bool | None): Whether the role is hoisted in the user list.
            managed (bool | None): Whether the role is managed by an external service.
            mentionable (bool | None): Whether the role is mentionable.
            mention (str | None): The mention string of the role.
            color (int | None): The color of the role.

        Returns:
            Roles | None: The updated role if found, None if the role does not exist.
        """

        return await self.table.update(
            where={"id": role_id},
            data={
                "name": role_name or "",
                "hoist": hoist or False,
                "managed": managed or False,
                "mentionable": mentionable or False,
                "mention": mention or "",
                "color": color or 0,
            },
        )

    async def sync_role(
        self,
        role_id: int,
        role_name: str,
        hoist: bool,
        managed: bool,
        mentionable: bool,
        mention: str,
        color: int,
        created_at: datetime,
    ) -> Roles | None:
        existing_role = await self.get_role_by_id(role_id)

        if existing_role is None:
            return await self.create_role(
                role_id=role_id,
                role_name=role_name,
                hoist=hoist,
                managed=managed,
                mentionable=mentionable,
                mention=mention,
                color=color,
                created_at=created_at,
            )

        if (
            existing_role.name != role_name
            or existing_role.hoist != hoist
            or existing_role.managed != managed
            or existing_role.mentionable != mentionable
            or existing_role.mention != mention
            or existing_role.color != color
            or existing_role.created_at != created_at
        ):
            return await self.update_role(
                role_id=role_id,
                role_name=role_name if existing_role.name != role_name else None,
                hoist=hoist if existing_role.hoist != hoist else None,
                managed=managed if existing_role.managed != managed else None,
                mentionable=mentionable if existing_role.mentionable != mentionable else None,
                mention=mention if existing_role.mention != mention else None,
                color=color if existing_role.color != color else None,
            )

        return existing_role

    async def delete_role(self, role_id: int) -> None:
        """
        Deletes a role from the database based on the specified role ID.

        Args:
            role_id (int): The ID of the role to delete.
        """

        await self.table.delete(where={"id": role_id})
