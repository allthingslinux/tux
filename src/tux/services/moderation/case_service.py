"""
Case service for moderation operations.

This service handles case creation, retrieval, and management using
the existing database controllers and proper dependency injection.
"""

from typing import Any

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

        Args:
            case_controller: Database controller for case operations
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

        Args:
            guild_id: ID of the guild
            user_id: ID of the target user
            moderator_id: ID of the moderator
            case_type: Type of moderation action
            reason: Reason for the action
            **kwargs: Additional case data (use case_expires_at for expiration datetime)

        Returns
        -------
            The created case
        """
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

        Args:
            case_id: The case ID to retrieve

        Returns
        -------
            The case if found, None otherwise
        """
        return await self._case_controller.get_case_by_id(case_id)

    async def get_user_cases(self, user_id: int, guild_id: int) -> list[Case]:
        """
        Get all cases for a user in a guild.

        Args:
            user_id: The user ID
            guild_id: The guild ID

        Returns
        -------
            List of cases for the user
        """
        return await self._case_controller.get_cases_by_user(user_id, guild_id)

    async def get_active_cases(self, user_id: int, guild_id: int) -> list[Case]:
        """
        Get active cases for a user in a guild.

        Args:
            user_id: The user ID
            guild_id: The guild ID

        Returns
        -------
            List of active cases for the user
        """
        return await self._case_controller.get_active_cases_by_user(user_id, guild_id)
