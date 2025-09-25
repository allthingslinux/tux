from collections.abc import Sequence
from typing import Any, ClassVar

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.database.models import CaseType as DBCaseType
from tux.services.moderation import ModerationCoordinator

__all__ = ["ModerationCogBase"]


class ModerationCogBase(BaseCog):
    """Base class for moderation cogs with proper dependency injection.

    This class provides a foundation for moderation cogs by injecting the
    ModerationCoordinator service through the DI container. All moderation
    logic is handled by dedicated services.

    Attributes
    ----------
    moderation : ModerationCoordinator
        The main service for handling moderation operations
    """

    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[DBCaseType]] = {DBCaseType.BAN, DBCaseType.KICK, DBCaseType.TEMPBAN}

    def __init__(self, bot: Tux) -> None:
        """Initialize the moderation cog base."""
        super().__init__(bot)
        # Note: ModerationCoordinator will be initialized when needed
        self.moderation: ModerationCoordinator | None = None

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
        """Execute moderation action using the service architecture."""
        if self.moderation is None:
            msg = "Moderation service not initialized"
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
        """Check if a user is jailed."""
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        return bool(latest_case and latest_case.case_type == DBCaseType.JAIL)

    async def is_pollbanned(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is poll banned."""
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        return bool(latest_case and latest_case.case_type == DBCaseType.POLLBAN)

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is snippet banned."""
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
        )
        return bool(latest_case and latest_case.case_type == DBCaseType.SNIPPETBAN)
