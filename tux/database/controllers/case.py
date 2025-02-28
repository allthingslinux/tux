from datetime import UTC, datetime

from prisma.enums import CaseType
from prisma.models import Case
from prisma.types import CaseWhereInput
from tux.database.client import db


class CaseController:
    def __init__(self):
        self.table = db.case
        self.guild_table = db.guild

    async def get_next_case_number(self, guild_id: int) -> int:
        """
        Get the next case number for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the next case number for.

        Returns
        -------
        int
            The next case number for the guild.
        """

        # Try to update existing guild's case count
        guild = await self.guild_table.update(
            where={"guild_id": guild_id},
            data={"case_count": {"increment": 1}},
        )

        if guild is not None:
            return guild.case_count

        # If guild doesn't exist, create it with case_count = 1
        guild = await self.guild_table.create(
            data={"guild_id": guild_id, "case_count": 1},
        )

        return guild.case_count

    async def insert_case(
        self,
        guild_id: int,
        case_user_id: int,
        case_moderator_id: int,
        case_type: CaseType,
        case_reason: str,
        case_user_roles: list[int] | None = None,
        case_expires_at: datetime | None = None,
        case_tempban_expired: bool = False,
    ) -> Case:
        """
        Insert a case into the database.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to insert the case into.
        case_user_id : int
            The ID of the target of the case.
        case_moderator_id : int
            The ID of the moderator of the case.
        case_type : CaseType
            The type of the case.
        case_reason : str
            The reason for the case.
        case_user_roles : list[int] | None
            The roles of the target of the case.
        case_expires_at : datetime | None
            The expiration date of the case.
        case_tempban_expired : bool
            Whether the tempban has expired (Use only for tempbans).

        Returns
        -------
        Case
            The case database object.
        """

        case_number = await self.get_next_case_number(guild_id)

        # Create the case with the atomically incremented case number
        return await self.table.create(
            data={
                "case_number": case_number,
                "case_user_id": case_user_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
                "case_reason": case_reason,
                "case_expires_at": case_expires_at,
                "case_user_roles": case_user_roles if case_user_roles is not None else [],
                "case_tempban_expired": case_tempban_expired,
                "guild": {
                    "connect": {
                        "guild_id": guild_id,
                    },
                },
            },
            include={
                "guild": True,
            },
        )

    async def get_all_cases(self, guild_id: int) -> list[Case]:
        """
        Get all cases for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.

        Returns
        -------
        list[Case]
            A list of cases for the guild.
        """

        return await self.table.find_many(
            where={"guild_id": guild_id},
            order={"case_created_at": "desc"},
        )

    async def get_cases_by_options(
        self,
        guild_id: int,
        options: CaseWhereInput,
    ) -> list[Case] | None:
        """
        Get cases for a guild by options.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        options : CaseWhereInput
            The options to filter cases by.

        Returns
        -------
        list[Case] | None
            A list of cases for the guild if found, otherwise None.
        """

        return await self.table.find_many(
            where={"guild_id": guild_id, **options},
            order={"case_created_at": "desc"},
        )

    async def get_case_by_number(self, guild_id: int, case_number: int) -> Case | None:
        """
        Get a case by its number in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the case in.
        case_number : int
            The number of the case to get.

        Returns
        -------
        Case | None
            The case if found, otherwise None.
        """

        return await self.table.find_first(
            where={"guild_id": guild_id, "case_number": case_number},
        )

    async def get_all_cases_by_user_id(
        self,
        guild_id: int,
        case_user_id: int,
    ) -> list[Case]:
        """
        Get all cases for a target in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        case_user_id : int
            The ID of the target to get cases for.

        Returns
        -------
        list[Case]
            A list of cases for the target in the guild.
        """

        return await self.table.find_many(
            where={"guild_id": guild_id, "case_user_id": case_user_id},
            order={"case_created_at": "desc"},
        )

    async def get_all_cases_by_moderator_id(
        self,
        guild_id: int,
        case_moderator_id: int,
    ) -> list[Case]:
        """
        Get all cases for a moderator in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        case_moderator_id : int
            The ID of the moderator to get cases for.

        Returns
        -------
        list[Case]
            A list of cases for the moderator in the guild.
        """

        return await self.table.find_many(
            where={"guild_id": guild_id, "case_moderator_id": case_moderator_id},
            order={"case_created_at": "desc"},
        )

    async def get_all_cases_by_type(self, guild_id: int, case_type: CaseType) -> list[Case]:
        """
        Get all cases of a type in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        case_type : CaseType
            The type of case to get.

        Returns
        -------
        list[Case]
            A list of cases of the type in the guild.
        """

        return await self.table.find_many(
            where={"guild_id": guild_id, "case_type": case_type},
            order={"case_created_at": "desc"},
        )

    async def get_last_jail_case_by_user_id(
        self,
        guild_id: int,
        case_user_id: int,
    ) -> Case | None:
        """
        Get the last jail case for a user.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the case in.
        case_user_id : int
            The ID of the user to get the case for.

        Returns
        -------
        Case | None
            The case if found, otherwise None.
        """

        return await self.table.find_first(
            where={"guild_id": guild_id, "case_user_id": case_user_id, "case_type": CaseType.JAIL},
            order={"case_created_at": "desc"},
        )

    async def update_case(
        self,
        guild_id: int,
        case_number: int,
        case_reason: str,
        case_status: bool | None = None,
    ) -> Case | None:
        """
        Update a case.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to update the case in.
        case_number : int
            The number of the case to update.
        case_reason : str
            The new reason for the case.
        case_status : bool | None
            The new status for the case.

        Returns
        -------
        Case | None
            The updated case if found, otherwise None.
        """

        case = await self.table.find_first(
            where={"guild_id": guild_id, "case_number": case_number},
        )

        if case is None:
            return None

        return await self.table.update(
            where={"case_id": case.case_id},
            data={"case_reason": case_reason, "case_status": case_status},
        )

    async def get_latest_case_by_user(
        self,
        guild_id: int,
        user_id: int,
        case_types: list[CaseType],
    ) -> Case | None:
        """
        Get the latest case for a user with specified case types.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the case in.
        user_id : int
            The ID of the user to get the case for.
        case_types : list[CaseType]
            The types of cases to search for.

        Returns
        -------
        Case | None
            The latest case if found, otherwise None.
        """

        cases = await self.table.find_many(
            where={"guild_id": guild_id, "case_user_id": user_id},
            order={"case_created_at": "desc"},
            take=1,
        )
        if not cases:
            return None

        case = cases[0]

        return case if case.case_type in case_types else None

    async def delete_case_by_number(self, guild_id: int, case_number: int) -> Case | None:
        """
        Delete a case by its number in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete the case in.
        case_number : int
            The number of the case to delete.

        Returns
        -------
        Case | None
            The case if found and deleted, otherwise None.
        """

        case = await self.table.find_first(
            where={"guild_id": guild_id, "case_number": case_number},
        )

        if case is not None:
            return await self.table.delete(where={"case_id": case.case_id})

        return None

    async def get_expired_tempbans(self) -> list[Case]:
        """
        Get all cases that have expired tempbans.

        Returns
        -------
        list[Case]
            A list of cases of the type in the guild.
        """

        return await self.table.find_many(
            where={
                "case_type": CaseType.TEMPBAN,
                "case_expires_at": {"lt": datetime.now(UTC)},
                "case_tempban_expired": False,
            },
        )

    async def set_tempban_expired(self, case_number: int | None, guild_id: int) -> int | None:
        """
        Set a tempban case as expired.

        Parameters
        ----------
        case_number : int
            The number of the case to update.
        guild_id : int
            The ID of the guild the case belongs to.

        Returns
        -------
        Optional[int]
            The number of Case records updated (1) if successful, None if no records were found,
            or raises an exception if multiple records were affected.
        """

        if case_number is None:
            msg = "Case number not found"
            raise ValueError(msg)

        result = await self.table.update_many(
            where={"case_number": case_number, "guild_id": guild_id},
            data={"case_tempban_expired": True},
        )

        if result == 1:
            return result
        if result == 0:
            return None

        msg = f"Multiple records ({result}) were affected when updating case {case_number} in guild {guild_id}"

        raise ValueError(msg)
