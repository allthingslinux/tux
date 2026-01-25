"""
Case service for moderation operations.

This service handles case creation, retrieval, and management using
the existing database controllers and proper dependency injection.
"""

from typing import Any

from loguru import logger

from tux.database.controllers.case import CaseController
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType


class CaseService:
    """
    Service for managing moderation cases.

    Provides clean, testable methods for case operations without
    the complexity of mixin inheritance.
    """

    def __init__(self, case_controller: CaseController):
        """
        Initialize the case service.

        Parameters
        ----------
        case_controller : CaseController
            Database controller for case operations.
        """
        self._case_controller = case_controller

    async def create_case(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        case_type: DBCaseType,
        reason: str,
        **kwargs: Any,
    ) -> Case:
        """
        Create a new moderation case.

        Parameters
        ----------
        guild_id : int
            ID of the guild.
        user_id : int
            ID of the target user.
        moderator_id : int
            ID of the moderator.
        case_type : DBCaseType
            Type of moderation action.
        reason : str
            Reason for the action.
        **kwargs : Any
            Additional case data (use case_expires_at for expiration datetime).

        Returns
        -------
        Case
            The created case.
        """
        logger.debug(f"CaseService.create_case called with kwargs: {kwargs}")

        return await self._case_controller.create_case(
            case_type=case_type.value,
            case_user_id=user_id,
            case_moderator_id=moderator_id,
            guild_id=guild_id,
            case_reason=reason,
            **kwargs,
        )

    async def get_case(self, case_id: int) -> Case | None:
        """
        Get a case by ID.

        Parameters
        ----------
        case_id : int
            The case ID to retrieve.

        Returns
        -------
        Case | None
            The case if found, None otherwise.
        """
        return await self._case_controller.get_case_by_id(case_id)

    async def get_user_cases(self, user_id: int, guild_id: int) -> list[Case]:
        """
        Get all cases for a user in a guild.

        Parameters
        ----------
        user_id : int
            The user ID.
        guild_id : int
            The guild ID.

        Returns
        -------
        list[Case]
            List of cases for the user.
        """
        return await self._case_controller.get_cases_by_user(user_id, guild_id)

    async def get_active_cases(self, user_id: int, guild_id: int) -> list[Case]:
        """
        Get active cases for a user in a guild.

        Parameters
        ----------
        user_id : int
            The user ID.
        guild_id : int
            The guild ID.

        Returns
        -------
        list[Case]
            List of active cases for the user.
        """
        return await self._case_controller.get_active_cases_by_user(user_id, guild_id)

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
        return await self._case_controller.update_mod_log_message_id(
            case_id,
            message_id,
        )

    async def void_case(
        self,
        case_id: int,
        failure_reason: str | None = None,
    ) -> Case | None:
        """
        Void a case by setting its status to False.

        Used when a case was created but the Discord action failed,
        preserving the audit trail while marking it as invalid.

        Parameters
        ----------
        case_id : int
            The case ID to void.
        failure_reason : str | None, optional
            Optional reason for voiding (e.g., "Discord action failed").
            Will be appended to the existing case reason.

        Returns
        -------
        Case | None
            The voided case, or None if not found.
        """
        # Get the case first to preserve the original reason
        case = await self._case_controller.get_case_by_id(case_id)
        if case is None:
            return None

        # Build updated reason with failure information
        updated_reason = case.case_reason
        if failure_reason:
            # Append failure reason, respecting max length (2000 chars)
            failure_note = f" [VOIDED: {failure_reason}]"
            if len(updated_reason) + len(failure_note) <= 2000:
                updated_reason = updated_reason + failure_note
            else:
                # Truncate original reason if needed to fit failure note
                max_original_length = 2000 - len(failure_note)
                updated_reason = updated_reason[:max_original_length] + failure_note

        # Update both status and reason
        return await self._case_controller.update_by_id(
            case_id,
            case_status=False,
            case_reason=updated_reason,
        )
