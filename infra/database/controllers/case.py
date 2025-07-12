from datetime import UTC, datetime
from typing import Any

from database.client import db
from database.controllers.base import BaseController

from prisma.actions import GuildActions
from prisma.enums import CaseType
from prisma.models import Case, Guild
from prisma.types import CaseWhereInput


class CaseController(BaseController[Case]):
    """Controller for managing moderation cases.

    This controller provides methods for creating, retrieving, updating,
    and deleting moderation cases in the database.
    """

    def __init__(self):
        """Initialize the CaseController with the case table."""
        super().__init__("case")
        # Access guild table through client property
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_next_case_number(self, guild_id: int) -> int:
        """Get the next case number for a guild.

        This method automatically handles guild creation if it doesn't exist
        and atomically increments the case counter.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the next case number for.

        Returns
        -------
        int
            The next case number for the guild.
        """
        # Use connect_or_create to ensure guild exists and increment case count
        guild = await self.guild_table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "case_count": 1},
                "update": {"case_count": {"increment": 1}},
            },
        )

        return self.safe_get_attr(guild, "case_count", 1)

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
        """Insert a case into the database.

        This method automatically handles guild creation if needed using
        connect_or_create for optimal performance and race condition prevention.

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

        # Create case with relation to guild using connect_or_create
        return await self.create(
            data={
                "case_number": case_number,
                "case_user_id": case_user_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
                "case_reason": case_reason,
                "case_expires_at": case_expires_at,
                "case_user_roles": case_user_roles if case_user_roles is not None else [],
                "case_tempban_expired": case_tempban_expired,
                "guild": self.connect_or_create_relation("guild_id", guild_id),
            },
            include={"guild": True},
        )

    async def get_case_by_id(self, case_id: int, include_guild: bool = False) -> Case | None:
        """Get a case by its primary key ID.

        Parameters
        ----------
        case_id : int
            The primary key ID of the case
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        Case | None
            The case if found, otherwise None
        """
        include = {"guild": True} if include_guild else None
        return await self.find_unique(where={"case_id": case_id}, include=include)

    async def get_all_cases(self, guild_id: int) -> list[Case]:
        """Get all cases for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.

        Returns
        -------
        list[Case]
            A list of cases for the guild.
        """
        return await self.find_many(
            where={"guild_id": guild_id},
            order={"case_created_at": "desc"},
        )

    async def get_cases_by_options(
        self,
        guild_id: int,
        options: CaseWhereInput,
    ) -> list[Case]:
        """Get cases for a guild by options.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        options : CaseWhereInput
            The options to filter cases by.

        Returns
        -------
        list[Case]
            A list of cases for the guild matching the criteria.
        """
        return await self.find_many(where={"guild_id": guild_id, **options}, order={"case_created_at": "desc"})

    async def get_case_by_number(self, guild_id: int, case_number: int, include_guild: bool = False) -> Case | None:
        """Get a case by its number in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the case in.
        case_number : int
            The number of the case to get.
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        Case | None
            The case if found, otherwise None.
        """
        include = {"guild": True} if include_guild else None
        return await self.find_one(where={"guild_id": guild_id, "case_number": case_number}, include=include)

    async def get_all_cases_by_user_id(
        self,
        guild_id: int,
        case_user_id: int,
        limit: int | None = None,
        include_guild: bool = False,
    ) -> list[Case]:
        """Get all cases for a target in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        case_user_id : int
            The ID of the target to get cases for.
        limit : int | None
            Optional limit on the number of cases to return
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        list[Case]
            A list of cases for the target in the guild.
        """
        include = {"guild": True} if include_guild else None
        return await self.find_many(
            where={"guild_id": guild_id, "case_user_id": case_user_id},
            include=include,
            take=limit,
            order={"case_created_at": "desc"},
        )

    async def get_all_cases_by_moderator_id(
        self,
        guild_id: int,
        case_moderator_id: int,
        limit: int | None = None,
    ) -> list[Case]:
        """Get all cases for a moderator in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get cases for.
        case_moderator_id : int
            The ID of the moderator to get cases for.
        limit : int | None
            Optional limit on the number of cases to return

        Returns
        -------
        list[Case]
            A list of cases for the moderator in the guild.
        """
        return await self.find_many(
            where={"guild_id": guild_id, "case_moderator_id": case_moderator_id},
            take=limit,
            order={"case_created_at": "desc"},
        )

    async def get_latest_case_by_user(
        self,
        guild_id: int,
        user_id: int,
        case_types: list[CaseType],
    ) -> Case | None:
        """Get the latest case for a user with specified case types.

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

        # Using a transaction to ensure read consistency
        async def get_latest_case():
            cases = await self.find_many(
                where={"guild_id": guild_id, "case_user_id": user_id},
                order={"case_created_at": "desc"},
                take=1,
            )

            if not cases:
                return None

            case = cases[0]
            case_type = self.safe_get_attr(case, "case_type")

            return case if case_type in case_types else None

        return await self.execute_transaction(get_latest_case)

    async def update_case(
        self,
        guild_id: int,
        case_number: int,
        case_reason: str,
        case_status: bool | None = None,
    ) -> Case | None:
        """Update a case.

        This method uses a transaction to ensure atomicity of the lookup and update.

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

        # Use a transaction to ensure the lookup and update are atomic
        async def update_case_tx():
            case = await self.find_one(where={"guild_id": guild_id, "case_number": case_number})
            if case is None:
                return None

            case_id = self.safe_get_attr(case, "case_id")
            update_data: dict[str, Any] = {"case_reason": case_reason}

            if case_status is not None:
                update_data["case_status"] = case_status

            return await self.update(where={"case_id": case_id}, data=update_data)

        return await self.execute_transaction(update_case_tx)

    async def delete_case_by_number(self, guild_id: int, case_number: int) -> Case | None:
        """Delete a case by its number in a guild.

        This method uses a transaction to ensure atomicity of the lookup and delete.

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

        # Use a transaction to ensure the lookup and delete are atomic
        async def delete_case_tx():
            case = await self.find_one(where={"guild_id": guild_id, "case_number": case_number})
            if case is None:
                return None

            case_id = self.safe_get_attr(case, "case_id")
            return await self.delete(where={"case_id": case_id})

        return await self.execute_transaction(delete_case_tx)

    async def get_expired_tempbans(self) -> list[Case]:
        """Get all cases that have expired tempbans.

        Returns
        -------
        list[Case]
            A list of cases with expired tempbans.
        """
        return await self.find_many(
            where={
                "case_type": CaseType.TEMPBAN,
                "case_expires_at": {"lt": datetime.now(UTC)},
                "case_tempban_expired": False,
            },
        )

    async def set_tempban_expired(self, case_number: int | None, guild_id: int) -> int | None:
        """Set a tempban case as expired.

        Parameters
        ----------
        case_number : int | None
            The number of the case to update.
        guild_id : int
            The ID of the guild the case belongs to.

        Returns
        -------
        int | None
            The number of Case records updated (1) if successful, None if no records were found,
            or raises an exception if multiple records were affected.
        """
        if case_number is None:
            msg = "Case number not found"
            raise ValueError(msg)

        result = await self.update_many(
            where={"case_number": case_number, "guild_id": guild_id},
            data={"case_tempban_expired": True},
        )

        if result == 1:
            return result
        if result == 0:
            return None

        msg = f"Multiple records ({result}) were affected when updating case {case_number} in guild {guild_id}"
        raise ValueError(msg)

    async def bulk_delete_cases_by_guild_id(self, guild_id: int) -> int:
        """Delete all cases for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete cases for

        Returns
        -------
        int
            The number of cases deleted
        """
        return await self.delete_many(where={"guild_id": guild_id})

    async def count_cases_by_guild_id(self, guild_id: int) -> int:
        """Count the number of cases in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to count cases for

        Returns
        -------
        int
            The number of cases in the guild
        """
        return await self.count(where={"guild_id": guild_id})

    async def count_cases_by_user_id(self, guild_id: int, user_id: int) -> int:
        """Count the number of cases for a user in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to count cases for
        user_id : int
            The ID of the user to count cases for

        Returns
        -------
        int
            The number of cases for the user in the guild
        """
        return await self.count(where={"guild_id": guild_id, "case_user_id": user_id})

    async def is_user_under_restriction(
        self,
        guild_id: int,
        user_id: int,
        active_restriction_type: CaseType,
        inactive_restriction_type: CaseType,
    ) -> bool:
        """Check if a user is currently under a specific restriction.

        The user is considered under restriction if their latest relevant case
        (of either active_restriction_type or inactive_restriction_type) is
        of the active_restriction_type.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.
        active_restriction_type : CaseType
            The case type that signifies an active restriction (e.g., BAN, JAIL).
        inactive_restriction_type : CaseType
            The case type that signifies the removal of the restriction (e.g., UNBAN, UNJAIL).

        Returns
        -------
        bool
            True if the user is under the specified restriction, False otherwise.
        """
        latest_case = await self.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
            case_types=[active_restriction_type, inactive_restriction_type],
        )

        if not latest_case:
            return False  # No relevant cases, so not under active restriction

        return latest_case.case_type == active_restriction_type
