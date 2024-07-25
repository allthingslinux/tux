from datetime import datetime

from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case, Guild
from prisma.types import CaseWhereInput
from tux.database.client import db


class CaseController:
    def __init__(self):
        self.table = db.case
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild:
        """
        Ensure a guild exists in the database and return the found or created object.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to ensure exists.

        Returns
        -------
        Guild
            The guild database object.
        """
        guild = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    """
    CREATE
    """

    async def insert_case(
        self,
        guild_id: int,
        case_target_id: int,
        case_moderator_id: int,
        case_type: CaseType,
        case_reason: str,
        case_target_roles: list[int] | None = None,
        case_expires_at: datetime | None = None,
    ) -> Case:
        """
        Insert a case into the database.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to insert the case into.
        case_target_id : int
            The ID of the target of the case.
        case_moderator_id : int
            The ID of the moderator of the case.
        case_type : CaseType
            The type of the case.
        case_reason : str
            The reason for the case.
        case_target_roles : list[int] | None
            The roles of the target of the case.
        case_expires_at : datetime | None
            The expiration date of the case.

        Returns
        -------
        Case
            The case database object.
        """
        await self.ensure_guild_exists(guild_id)

        return await self.table.create(
            data={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
                "case_reason": case_reason,
                "case_number": await self.table.count(where={"guild_id": guild_id}) + 1,
                "case_expires_at": case_expires_at,
                "case_target_roles": case_target_roles if case_target_roles is not None else [],
            },
        )

    """
    READ
    """

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
        return await self.table.find_many(where={"guild_id": guild_id}, order={"case_created_at": "desc"})

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
        cases = await self.table.find_many(where={"guild_id": guild_id, **options}, order={"case_created_at": "desc"})
        logger.info(cases)
        return cases

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
        return await self.table.find_first(where={"guild_id": guild_id, "case_number": case_number})

    async def get_all_cases_by_target_id(self, guild_id: int, case_target_id: int) -> list[Case]:
        """
        Get all cases for a target in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        case_target_id : int
            The ID of the target to get cases for.

        Returns
        -------
        list[Case]
            A list of cases for the target in the guild.
        """
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_target_id": case_target_id},
            order={"case_created_at": "desc"},
        )

    async def get_all_cases_by_moderator_id(self, guild_id: int, case_moderator_id: int) -> list[Case]:
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

    async def get_last_jail_case_by_target_id(
        self,
        guild_id: int,
        case_target_id: int,
    ) -> Case | None:
        return await self.table.find_first(
            where={"guild_id": guild_id, "case_target_id": case_target_id, "case_type": CaseType.JAIL},
            order={"case_created_at": "desc"},
        )

    """
    UPDATE
    """

    async def update_case(
        self,
        guild_id: int,
        case_number: int,
        case_reason: str,
        case_status: bool | None = None,
    ) -> Case | None:
        case = await self.table.find_first(where={"guild_id": guild_id, "case_number": case_number})
        if case is None:
            return None
        return await self.table.update(
            where={"case_id": case.case_id},
            data={"case_reason": case_reason, "case_status": case_status},
        )

    async def update_case_numbers(self) -> None:
        # for every guild in the database get all cases and update the case_number based on the order
        guilds = await self.guild_table.find_many()
        for guild in guilds:
            cases = await self.table.find_many(where={"guild_id": guild.guild_id}, order={"case_created_at": "asc"})
            for index, case in enumerate(cases):
                await self.table.update(where={"case_id": case.case_id}, data={"case_number": index + 1})

    async def update_case_numbers_for_guild(self, guild_id: int) -> None:
        cases = await self.table.find_many(where={"guild_id": guild_id}, order={"case_created_at": "asc"})
        for index, case in enumerate(cases):
            await self.table.update(where={"case_id": case.case_id}, data={"case_number": index + 1})

    """
    DELETE
    """

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
        case = await self.table.find_first(where={"guild_id": guild_id, "case_number": case_number})
        if case is not None:
            return await self.table.delete(where={"case_id": case.case_id})
        return None
