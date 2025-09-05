"""
Status checking for moderation restrictions.

Handles checking if users are under various moderation restrictions like jail, pollban, snippetban.
"""

from tux.database.models import CaseType as DBCaseType


class StatusChecker:
    """
    Checks user status for various moderation restrictions.

    This mixin provides functionality to:
    - Check if a user is jailed
    - Check if a user is poll banned
    - Check if a user is snippet banned
    - Query the database for active restrictions
    """

    async def is_pollbanned(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is poll banned.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is poll banned, False otherwise.
        """
        # Get latest case for this user
        db = getattr(self, "db", None)
        if not db:
            return False
        return await db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,
            inactive_restriction_type=DBCaseType.UNJAIL,
        )

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is snippet banned.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is snippet banned, False otherwise.
        """
        # Get latest case for this user
        db = getattr(self, "db", None)
        if not db:
            return False
        return await db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,
            inactive_restriction_type=DBCaseType.UNJAIL,
        )

    async def is_jailed(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is jailed using the optimized latest case method.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is jailed, False otherwise.
        """
        # Get latest case for this user
        db = getattr(self, "db", None)
        if not db:
            return False
        return await db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=DBCaseType.JAIL,
            inactive_restriction_type=DBCaseType.UNJAIL,
        )
