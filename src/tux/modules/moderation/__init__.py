from typing import Any, ClassVar

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.types import Tux
from tux.database.models import CaseType as DBCaseType
from tux.services.moderation.case_executor import CaseExecutor
from tux.services.moderation.case_response_handler import CaseResponseHandler
from tux.services.moderation.condition_checker import ConditionChecker
from tux.services.moderation.dm_handler import DMHandler
from tux.services.moderation.embed_manager import EmbedManager
from tux.services.moderation.lock_manager import LockManager
from tux.services.moderation.moderation_service import ModerationService
from tux.services.moderation.status_checker import StatusChecker

__all__ = ["ModerationCogBase"]


class ModerationCogBase(  # type: ignore
    BaseCog,
    LockManager,
    DMHandler,
    CaseExecutor,
    CaseResponseHandler,
    EmbedManager,
    ConditionChecker,
    StatusChecker,
):
    """Main moderation cog base class combining all moderation functionality.

    This class uses multiple inheritance to compose functionality from focused mixins
    for better maintainability and separation of concerns. Each mixin handles a
    specific aspect of moderation operations.

    Parameters
    ----------
    bot : Tux
        The bot instance
    """

    # Mixin attributes (provided by composition)
    # db property inherited from BaseCog  # type: ignore

    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[DBCaseType]] = {DBCaseType.BAN, DBCaseType.KICK, DBCaseType.TEMPBAN}

    def __init__(self, bot: Tux) -> None:
        """Initialize the moderation cog base with all mixin functionality.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance that will be passed to all mixins.

        Notes
        -----
        This method calls the parent class constructors in method resolution order,
        ensuring all mixin functionality is properly initialized. It also creates
        a ModerationService instance for advanced moderation operations.
        """
        super().__init__(bot)

        # Initialize the comprehensive moderation service
        self.moderation_service = ModerationService(bot, self.db)

        # For backward compatibility, expose service methods directly
        # This allows existing code to work while providing access to advanced features
        self.execute_moderation_action = self.moderation_service.execute_moderation_action
        self.get_system_status = self.moderation_service.get_system_status
        self.cleanup_old_data = self.moderation_service.cleanup_old_data

    async def moderate_user(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        silent: bool = False,
        dm_action: str | None = None,
        actions: list[tuple[Any, type[Any]]] | None = None,
        duration: str | None = None,
        expires_at: int | None = None,
    ) -> None:
        """
        Convenience method for moderation actions using the advanced service.

        This method provides a simple interface that automatically uses all the
        advanced features: retry logic, circuit breakers, monitoring, etc.

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
        actions : list[tuple[Any, type[Any]]] | None
            Discord API actions to execute
        duration : str | None
            Duration string for display
        expires_at : int | None
            Expiration timestamp

        Examples
        --------
        >>> # Simple ban command
        >>> await self.moderate_user(
        ...     ctx, DBCaseType.BAN, member, "Spam", actions=[(ctx.guild.ban(member, reason="Spam"), type(None))]
        ... )

        >>> # Advanced usage with custom DM action
        >>> await self.moderate_user(
        ...     ctx, DBCaseType.TIMEOUT, member, "Breaking rules",
        ...     dm_action="timed out",
        ...     actions=[(member.timeout(datetime.now() + timedelta(hours=1))), type(None))]
        ... )
        """
        await self.moderation_service.execute_moderation_action(
            ctx=ctx,
            case_type=case_type,
            user=user,
            reason=reason,
            silent=silent,
            dm_action=dm_action,
            actions=actions or [],
            duration=duration,
            expires_at=expires_at,
        )
