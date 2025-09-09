from collections.abc import Sequence
from typing import Any, ClassVar

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.types import Tux
from tux.database.models import CaseType as DBCaseType
from tux.services.moderation import ModerationCoordinator

__all__ = ["ModerationCogBase"]


class ModerationCogBase(BaseCog):
    """Main moderation cog base class using service-based architecture.

    This class provides a foundation for moderation cogs by injecting the
    ModerationCoordinator service. All moderation logic is now handled by
    dedicated services with proper dependency injection.

    Parameters
    ----------
    bot : Tux
        The bot instance

    Attributes
    ----------
    moderation : ModerationCoordinator
        The main service for handling moderation operations

    Methods
    -------
    is_jailed(guild_id: int, user_id: int) -> bool
        Check if a user is currently jailed in the specified guild
    is_pollbanned(guild_id: int, user_id: int) -> bool
        Check if a user is currently poll banned in the specified guild
    is_snippetbanned(guild_id: int, user_id: int) -> bool
        Check if a user is currently snippet banned in the specified guild
    """

    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[DBCaseType]] = {DBCaseType.BAN, DBCaseType.KICK, DBCaseType.TEMPBAN}

    # Moderation coordinator service (injected)
    moderation: ModerationCoordinator | None

    def __init__(self, bot: Tux, moderation_coordinator: ModerationCoordinator | None = None) -> None:
        """Initialize the moderation cog base with service injection.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance
        moderation_coordinator : ModerationCoordinator, optional
            The moderation coordinator service. If not provided, will be injected from container.

        Notes
        -----
        This method injects the ModerationCoordinator service from the DI container,
        providing access to all moderation functionality through a clean service interface.
        """
        super().__init__(bot)

        # Inject the moderation coordinator service
        if moderation_coordinator is not None:
            self.moderation = moderation_coordinator
        else:
            # Get from container if available, otherwise create a fallback
            try:
                container = getattr(self, "container", None)
                self.moderation = container.get(ModerationCoordinator) if container is not None else None
            except Exception:
                # Fallback for cases where container is not available
                # This will be replaced when services are properly registered
                self.moderation = None

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
    ) -> None:
        """
        Convenience method for moderation actions using the service-based architecture.

        This method provides a simple interface that delegates to the ModerationCoordinator
        service, which handles all the advanced features: retry logic, circuit breakers,
        error handling, and case management.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        case_type : DBCaseType
            Type of moderation case
        user : discord.Member | discord.User
            Target user
        reason : str
            Reason for the action
        silent : bool
            Whether to send DM (default: False)
        dm_action : str | None
            DM action description (auto-generated if None)
        actions : Sequence[tuple[Any, type[Any]]] | None
            Discord API actions to execute with their expected return types
        duration : int | None
            Duration in seconds for temp actions

        Examples
        --------
        >>> # Simple ban command
        >>> await self.moderate_user(
        ...     ctx, DBCaseType.BAN, member, "Spam", actions=[(ctx.guild.ban(member, reason="Spam"), type(None))]
        ... )

        >>> # Timeout with duration
        >>> await self.moderate_user(
        ...     ctx,
        ...     DBCaseType.TIMEOUT,
        ...     member,
        ...     "Breaking rules",
        ...     dm_action="timed out",
        ...     actions=[(member.timeout, type(None))],
        ...     duration=3600,  # 1 hour in seconds
        ... )
        """
        if self.moderation is None:
            msg = "ModerationCoordinator service not available"
            raise RuntimeError(msg)

        await self.moderation.execute_moderation_action(
            ctx=ctx,
            case_type=case_type,
            user=user,
            reason=reason,
            silent=silent,
            dm_action=dm_action,
            actions=actions,
            duration=duration,
        )

    async def is_jailed(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is jailed.

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
        # Get latest case for this user (more efficient than counting all cases)
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # If no cases exist or latest case is an unjail, user is not jailed
        return bool(latest_case and latest_case.case_type == DBCaseType.JAIL)

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
        # Get latest case for this user (more efficient than counting all cases)
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # If no cases exist or latest case is a pollunban, user is not poll banned
        return bool(latest_case and latest_case.case_type == DBCaseType.POLLBAN)

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
        # Get latest case for this user (more efficient than counting all cases)
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )

        # If no cases exist or latest case is a snippetunban, user is not snippet banned
        return bool(latest_case and latest_case.case_type == DBCaseType.SNIPPETBAN)
