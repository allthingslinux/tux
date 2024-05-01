from datetime import datetime

from prisma.models import Roles
from tux.database.client import db


class RolesController:
    def __init__(self) -> None:
        """
        Initializes the controller and connects to the roles table in the database.
        """
        self.table = db.roles

    async def get_all_roles(self) -> list[Roles]:
        """
        Retrieves all roles from the database.

        Returns
        -------
        list[Roles]
            A list of all roles.
        """
        return await self.table.find_many()

    async def get_role_by_id(self, role_id: int) -> Roles | None:
        """
        Retrieves a role from the database based on the specified role ID.

        Parameters
        ----------
        role_id : int
            The ID of the role to retrieve.

        Returns
        -------
        Roles or None
            The role if found, otherwise None.
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
        Creates a new role in the database with the specified details.

        Parameters
        ----------
        role_id : int
            The ID assigned to the new role.
        role_name : str
            The name of the role.
        hoist : bool, optional
            Whether the role is hoisted (visible separately on the user list), by default False.
        managed : bool, optional
            Whether the role is managed by an external service, by default False.
        mentionable : bool, optional
            Whether the role is mentionable, by default False.
        created_at : datetime, optional
            The creation date of the role, by default None.
        mention : str, optional
            The mention string for the role, by default None.
        color : int, optional
            The display color of the role as an integer, by default None.

        Returns
        -------
        Roles
            The newly created role.
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
        Updates a role in the database with the specified parameters.

        Parameters
        ----------
        role_id : int
            The ID of the role to update.
        role_name : str or None, optional
            The new name of the role, if changing.
        hoist : bool or None, optional
            New hoist state if changing, else None.
        managed : bool or None, optional
            New managed state if changing, else None.
        mentionable : bool or None, optional
            New mentionable state if changing, else None.
        mention : str or None, optional
            New mention string if changing, else None.
        color : int or None, optional
            New color if changing, default to None if no change.

        Returns
        -------
        Roles or None
            The updated role if found and updated, otherwise None if the role does not exist.
        """
        return await self.table.update(
            where={"id": role_id},
            data={
                "name": role_name or "",
                "hoist": hoist if hoist is not None else False,
                "managed": managed if managed is not None else False,
                "mentionable": mentionable if mentionable is not None else False,
                "mention": mention or "",
                "color": color if color is not None else 0,
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
        """
        Synchronizes a role in the database with the specified parameters.

        Parameters
        ----------
        role_id : int
            The ID of the role to synchronize.
        role_name : str
            The name of the role.
        hoist : bool
            Whether the role is hoisted.
        managed : bool
            Whether the role is managed.
        mentionable : bool
            Whether the role is mentionable.
        mention : str
            The mention string for the role.
        color : int
            The color of the role.
        created_at : datetime
            The creation date of the role.

        Returns
        -------
        Roles | None
            The updated role if successful, otherwise None.
        """

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

        Parameters
        ----------
        role_id : int
            The ID of the role to delete.

        Returns
        -------
        None
        """
        await self.table.delete(where={"id": role_id})
