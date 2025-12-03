"""
Moderation Module for Tux Bot.

This module provides the foundation for all moderation-related functionality
in the Tux Discord bot, including base classes for moderation cogs and
common moderation utilities.
"""

from collections.abc import Sequence

# Type annotation import
from typing import TYPE_CHECKING, Any, ClassVar

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.database.models import CaseType as DBCaseType
from tux.services.moderation import ModerationServiceFactory

if TYPE_CHECKING:
    from tux.services.moderation import ModerationCoordinator

__all__ = ["ModerationCogBase"]


class ModerationCogBase(BaseCog):
    """Base class for moderation cogs with centralized service management.

    This class provides a foundation for moderation cogs with clean service
    initialization using a factory pattern. Services are created once during
    initialization and reused for all operations.

    Attributes
    ----------
    moderation : ModerationCoordinator
        The main service for handling moderation operations
    """

    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[DBCaseType]] = {
        DBCaseType.BAN,
        DBCaseType.KICK,
        DBCaseType.TEMPBAN,
    }

    def __init__(self, bot: Tux) -> None:
        """Initialize the moderation cog base with services.

        Parameters
        ----------
        bot : Tux
            The bot instance
        """
        super().__init__(bot)

        # Initialize moderation services using factory pattern
        # This avoids async initialization and duplicate service creation
        self.moderation: ModerationCoordinator = (
            ModerationServiceFactory.create_coordinator(bot, self.db.case)
        )

    async def moderate_user(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        silent: bool = False,
        dm_action: str | None = None,
        actions: Sequence[tuple[Any, type[Any]]] | None = None,
        duration: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Execute moderation action using the service architecture.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            Command context
        case_type : DBCaseType
            Type of moderation action
        user : discord.Member | discord.User
            Target user
        reason : str
            Reason for the action
        silent : bool, optional
            Whether to suppress DM to user, by default False
        dm_action : str | None, optional
            Custom DM action description, by default None
        actions : Sequence[tuple[Any, type[Any]]] | None, optional
            Discord API actions to execute, by default None
        duration : int | None, optional
            Duration in seconds for temporary actions, by default None
        **kwargs : Any
            Additional case data
        """
        await self.moderation.execute_moderation_action(
            ctx=ctx,
            case_type=case_type,
            user=user,
            reason=reason,
            silent=silent,
            dm_action=dm_action,
            actions=actions,
            duration=duration,
            **kwargs,
        )

    async def is_jailed(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is jailed.

        Parameters
        ----------
        guild_id : int
            Guild ID to check
        user_id : int
            User ID to check

        Returns
        -------
        bool
            True if user is jailed, False otherwise
        """
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        return bool(latest_case and latest_case.case_type == DBCaseType.JAIL)

    async def is_pollbanned(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is poll banned.

        Parameters
        ----------
        guild_id : int
            Guild ID to check
        user_id : int
            User ID to check

        Returns
        -------
        bool
            True if user is poll banned, False otherwise
        """
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        return bool(latest_case and latest_case.case_type == DBCaseType.POLLBAN)

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is snippet banned.

        Parameters
        ----------
        guild_id : int
            Guild ID to check
        user_id : int
            User ID to check

        Returns
        -------
        bool
            True if user is snippet banned, False otherwise
        """
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        return bool(latest_case and latest_case.case_type == DBCaseType.SNIPPETBAN)
