"""
Moderation case management controller.

This controller manages moderation cases (bans, kicks, timeouts, etc.) with
automatic case numbering, status tracking, and audit logging for Discord guilds.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import noload

from tux.database.controllers.base import BaseController
from tux.database.models import Case, Guild
from tux.database.models.enums import CaseType as DBCaseType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tux.database.service import DatabaseService


class CaseController(BaseController[Case]):
    """Clean Case controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the case controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Case, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_case_by_id(self, case_id: int) -> Case | None:
        """
        Get a case by its ID.

        Returns
        -------
        Case | None
            The case if found, None otherwise.
        """
        return await self.get_by_id(case_id)

    async def get_cases_by_user(self, user_id: int, guild_id: int) -> list[Case]:
        """
        Get all cases for a specific user in a guild.

        Returns
        -------
        list[Case]
            List of all cases for the user in the guild.
        """
        return await self.find_all(
            filters=(Case.case_user_id == user_id) & (Case.guild_id == guild_id),
        )

    async def get_active_cases_by_user(self, user_id: int, guild_id: int) -> list[Case]:
        """
        Get all active cases for a specific user in a guild.

        Returns
        -------
        list[Case]
            List of active cases for the user in the guild.
        """
        return await self.find_all(
            filters=(Case.case_user_id == user_id)
            & (Case.guild_id == guild_id)
            & (Case.case_status),
        )

    async def create_case(
        self,
        case_type: str,
        case_user_id: int,
        case_moderator_id: int,
        guild_id: int,
        case_reason: str | None = None,
        case_status: bool = True,
        **kwargs: Any,
    ) -> Case:
        """Create a new case with auto-generated case number.

        Uses SELECT FOR UPDATE to prevent race conditions when generating case numbers.

        Parameters
        ----------
        case_type : str
            The type of case (from CaseType enum value)
        case_user_id : int
            Discord ID of the user being moderated
        case_moderator_id : int
            Discord ID of the moderator
        guild_id : int
            Discord guild ID
        case_reason : str | None
            Reason for the moderation action
        case_status : bool
            Whether the case is active (default True)
        **kwargs : Any
            Additional case fields (e.g., case_expires_at, case_metadata, mod_log_message_id)

        Returns
        -------
        Case
            The newly created case with auto-generated case number.

        Notes
        -----
        - For expiring cases, use `case_expires_at` (datetime) in kwargs
        - Do NOT pass `duration` - convert to `case_expires_at` before calling this method
        - Case numbers are auto-generated per guild using SELECT FOR UPDATE locking
        """

        async def _create_with_lock(session: AsyncSession) -> Case:
            """Create a case with guild locking to prevent concurrent case numbering.

            Parameters
            ----------
            session : AsyncSession
                The database session to use for the operation.

            Returns
            -------
            Case
                The created case with auto-generated case number.
            """
            # Lock the guild row to prevent concurrent case number generation
            # Explicitly avoid loading relationships to prevent outer join issues with FOR UPDATE
            stmt = (
                select(Guild)
                .where(Guild.id == guild_id)  # type: ignore[arg-type]
                .options(noload("*"))  # Don't load any relationships
                .with_for_update()
            )
            result = await session.execute(stmt)
            guild = result.scalar_one_or_none()

            # Create guild if it doesn't exist
            if guild is None:
                guild = Guild(id=guild_id, case_count=0)
                session.add(guild)
                await session.flush()
                logger.debug(f"Created new guild {guild_id} with case_count=0")
            else:
                logger.debug(
                    f"Locked guild {guild_id} with case_count={guild.case_count}",
                )

            # Increment case count to get the next case number
            case_number = guild.case_count + 1
            guild.case_count = case_number
            logger.info(f"Generated case number {case_number} for guild {guild_id}")

            # Build case data dict
            case_data: dict[str, Any] = {
                "case_type": case_type,
                "case_user_id": case_user_id,
                "case_moderator_id": case_moderator_id,
                "guild_id": guild_id,
                "case_status": case_status,
                "case_number": case_number,
            }

            # Add optional reason if provided
            if case_reason is not None:
                case_data["case_reason"] = case_reason

            # Add any extra kwargs (like case_expires_at)
            logger.debug(f"Additional kwargs for case creation: {kwargs}")
            case_data.update(kwargs)

            # Create the case
            logger.trace(f"Creating Case object with data: {case_data}")
            case = Case(**case_data)
            session.add(case)
            await session.flush()
            await session.refresh(case)
            logger.success(
                f"Case created successfully: ID={case.id}, number={case.case_number}, expires_at={case.case_expires_at}",
            )
            return case

        return await self.with_session(_create_with_lock)

    async def update_case(self, case_id: int, **kwargs: Any) -> Case | None:
        """
        Update a case by ID.

        Returns
        -------
        Case | None
            The updated case, or None if not found.
        """
        return await self.update_by_id(case_id, **kwargs)

    async def update_mod_log_message_id(
        self,
        case_id: int,
        message_id: int,
    ) -> Case | None:
        """
        Update the mod log message ID for a case.

        Parameters
        ----------
        case_id : int
            The case ID to update.
        message_id : int
            The Discord message ID from the mod log.

        Returns
        -------
        Case | None
            The updated case, or None if not found.
        """
        return await self.update_by_id(case_id, mod_log_message_id=message_id)

    async def close_case(self, case_id: int) -> Case | None:
        """
        Close a case by setting its status to False.

        Returns
        -------
        Case | None
            The updated case, or None if not found.
        """
        return await self.update_by_id(case_id, case_status=False)

    async def delete_case(self, case_id: int) -> bool:
        """
        Delete a case by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(case_id)

    async def get_cases_by_guild(
        self,
        guild_id: int,
        limit: int | None = None,
    ) -> list[Case]:
        """
        Get all cases for a guild, optionally limited.

        Returns
        -------
        list[Case]
            List of cases for the guild.
        """
        return await self.find_all(filters=Case.guild_id == guild_id, limit=limit)

    async def get_cases_by_type(self, guild_id: int, case_type: str) -> list[Case]:
        """
        Get all cases of a specific type in a guild.

        Returns
        -------
        list[Case]
            List of cases matching the specified type.
        """
        return await self.find_all(
            filters=(Case.guild_id == guild_id) & (Case.case_type == case_type),
        )

    async def get_recent_cases(self, guild_id: int) -> list[Case]:
        """
        Get cases for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID to filter cases by.

        Returns
        -------
        list[Case]
            List of cases for the guild.

        Notes
        -----
        Time-based filtering is not yet implemented as the Case model lacks
        a created_at field. This currently returns all cases for the guild.
        """
        return await self.find_all(filters=Case.guild_id == guild_id)

    async def get_case_count_by_guild(self, guild_id: int) -> int:
        """
        Get the total number of cases in a guild.

        Returns
        -------
        int
            The total count of cases in the guild.
        """
        return await self.count(filters=Case.guild_id == guild_id)

    async def is_user_under_restriction(
        self,
        user_id: int | None = None,
        guild_id: int | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a user is under any active restriction in a guild.

        Returns
        -------
        bool
            True if user is under restriction, False otherwise.
        """
        # Handle both old and new parameter styles
        if user_id is None and "user_id" in kwargs:
            user_id = kwargs["user_id"]
        if guild_id is None and "guild_id" in kwargs:
            guild_id = kwargs["guild_id"]

        if user_id is None or guild_id is None:
            return False

        # For now, just check if user has any active cases
        # In the future, you can implement specific restriction type checking
        active_cases = await self.get_active_cases_by_user(user_id, guild_id)
        return bool(active_cases)

    async def get_case_by_number(self, case_number: int, guild_id: int) -> Case | None:
        """
        Get a case by its case number in a guild.

        Returns
        -------
        Case | None
            The case if found, None otherwise.
        """
        return await self.find_one(
            filters=(Case.case_number == case_number) & (Case.guild_id == guild_id),
        )

    async def get_cases_by_options(
        self,
        guild_id: int,
        options: dict[str, Any] | None = None,
    ) -> list[Case]:
        """
        Get cases by various filter options.

        Returns
        -------
        list[Case]
            List of cases matching the specified options.
        """
        filters = [Case.guild_id == guild_id]

        if options is None:
            options = {}

        # Add optional filters based on provided options
        if "user_id" in options:
            filters.append(Case.case_user_id == options["user_id"])
        if "moderator_id" in options:
            filters.append(Case.case_moderator_id == options["moderator_id"])
        if "case_type" in options:
            filters.append(Case.case_type == options["case_type"])
        if "status" in options:
            filters.append(Case.case_status == options["status"])

        # Combine all filters with AND
        combined_filter = filters[0]
        for filter_condition in filters[1:]:
            combined_filter = combined_filter & filter_condition

        return await self.find_all(filters=combined_filter)

    async def update_case_by_number(
        self,
        guild_id: int,
        case_number: int,
        **kwargs: Any,
    ) -> Case | None:
        """
        Update a case by guild ID and case number.

        Returns
        -------
        Case | None
            The updated case, or None if not found.
        """
        # Find the case first
        case = await self.get_case_by_number(case_number, guild_id)
        if case is None:
            return None

        # Update the case with the provided values
        return await self.update_by_id(case.id, **kwargs)

    async def get_all_cases(self, guild_id: int) -> list[Case]:
        """
        Get all cases in a guild.

        Returns
        -------
        list[Case]
            List of all cases in the guild.
        """
        return await self.find_all(filters=Case.guild_id == guild_id)

    async def get_latest_case_by_user(self, user_id: int, guild_id: int) -> Case | None:
        """
        Get the most recent case for a user in a guild.

        Returns
        -------
        Case | None
            The most recent case if found, None otherwise.
        """
        # Use database-level sorting for better performance
        # Sort by ID descending (assuming higher ID = newer case) and return the first one
        return await self.find_one(
            filters=(Case.case_user_id == user_id) & (Case.guild_id == guild_id),
            order_by=[Case.id.desc()],  # type: ignore[attr-defined]
        )

    async def set_tempban_expired(
        self,
        case_id: int,
        guild_id: int | None = None,
    ) -> bool:
        """
        Mark a tempban case as processed after the user has been unbanned.

        Parameters
        ----------
        case_id : int
            The case ID to mark as expired.
        guild_id : int | None, optional
            The guild ID (currently unused, kept for API consistency).

        This sets case_processed=True to indicate the expiration has been handled.
        The case_status remains True (the case is still valid, just completed).
        The case_expires_at field remains unchanged as a historical record.

        Returns
        -------
        bool
            True if the case was updated, False if not found
        """
        logger.debug(
            f"Marking tempban case {case_id} as processed (setting case_processed=True)",
        )
        result = await self.update_by_id(case_id, case_processed=True)
        success = result is not None
        if success:
            logger.debug(
                f"Case {case_id} marked as processed (case_processed=True, case_status unchanged)",
            )
        return success

    async def get_expired_tempbans(self, guild_id: int) -> list[Case]:
        """
        Get tempban cases that have expired but haven't been processed yet.

        Returns
        -------
        list[Case]
            List of expired unprocessed tempban cases where case_expires_at is in the past,
            case_processed=False, and case_status=True.
        """
        now = datetime.now(UTC)
        logger.trace(
            f"Checking for unprocessed expired tempbans in guild {guild_id}, current time: {now}",
        )

        # Find valid, unprocessed tempban cases where case_expires_at is in the past
        # Type ignore for SQLAlchemy comparison operators on nullable fields
        expired_cases = await self.find_all(
            filters=(
                (Case.guild_id == guild_id)
                & (Case.case_type == DBCaseType.TEMPBAN.value)
                & (Case.case_status == True)  # noqa: E712 - Valid cases only
                & (Case.case_processed == False)  # noqa: E712 - Not yet processed
                & (Case.case_expires_at.is_not(None))  # type: ignore[attr-defined]
                & (Case.case_expires_at < now)  # type: ignore[arg-type]
            ),
        )

        if expired_cases:
            # Only log if we found expired cases (INFO for actual work being done)
            logger.info(
                f"Found {len(expired_cases)} unprocessed expired tempbans in guild {guild_id}",
            )
            for case in expired_cases:
                logger.debug(
                    f"Unprocessed expired tempban: case_id={case.id}, user={case.case_user_id}, "
                    f"expires_at={case.case_expires_at}, processed={case.case_processed}",
                )
        else:
            # TRACE for routine checks that find nothing
            logger.trace(
                f"No unprocessed expired tempbans found in guild {guild_id}",
            )

        return expired_cases

    async def get_case_count_by_user(self, user_id: int, guild_id: int) -> int:
        """
        Get the total number of cases for a specific user in a guild.

        Returns
        -------
        int
            The total count of cases for the user.
        """
        return await self.count(
            filters=(Case.case_user_id == user_id) & (Case.guild_id == guild_id),
        )

    async def get_cases_by_moderator(
        self,
        moderator_id: int,
        guild_id: int,
    ) -> list[Case]:
        """
        Get all cases moderated by a specific user in a guild.

        Returns
        -------
        list[Case]
            List of cases moderated by the user.
        """
        return await self.find_all(
            filters=(Case.case_moderator_id == moderator_id)
            & (Case.guild_id == guild_id),
        )

    async def get_expired_cases(self, guild_id: int) -> list[Case]:
        """
        Get all expired cases (any type) that haven't been processed yet.

        Returns
        -------
        list[Case]
            List of expired unprocessed cases where case_expires_at is in the past,
            case_processed=False, and case_status=True.
        """
        now = datetime.now(UTC)

        # Find valid, unprocessed cases where case_expires_at is in the past
        # Type ignore for SQLAlchemy comparison operators on nullable fields
        return await self.find_all(
            filters=(
                (Case.guild_id == guild_id)
                & (Case.case_status == True)  # noqa: E712 - Valid cases only
                & (Case.case_processed == False)  # noqa: E712 - Not yet processed
                & (Case.case_expires_at.is_not(None))  # type: ignore[attr-defined]
                & (Case.case_expires_at < now)  # type: ignore[arg-type]
            ),
        )
