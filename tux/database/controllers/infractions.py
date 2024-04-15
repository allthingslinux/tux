from datetime import datetime

from prisma.models import Infractions
from tux.database.client import db
from tux.utils.enums import InfractionType


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
        expires_at: datetime | None = None,
    ) -> Infractions:
        """
        Creates a new infraction in the database with the specified user ID, moderator ID, infraction type, and reason.

        Args:
            user_id (int): The ID of the user for whom the infraction is created.
            moderator_id (int): The ID of the moderator who created the infraction.
            infraction_type (InfractionType): The type of the infraction.
            infraction_reason (str): The reason for the infraction.
            expires_at (datetime | None): The expiration date of the infraction.

        Returns:
            Infractions: The newly created infraction.
        """

        return await self.table.create(
            data={
                "user_id": user_id,
                "moderator_id": moderator_id,
                "infraction_type": infraction_type.value,
                "infraction_reason": infraction_reason,
                "expires_at": expires_at,
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
