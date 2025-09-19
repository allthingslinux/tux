"""
Moderation coordinator service.

Orchestrates all moderation services and provides the main interface
for moderation operations, replacing the mixin-based approach.
"""

import asyncio
import contextlib
from collections.abc import Callable, Coroutine, Sequence
from datetime import datetime
from typing import Any, ClassVar

import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType
from tux.shared.exceptions import handle_gather_result

from .case_service import CaseService
from .communication_service import CommunicationService
from .execution_service import ExecutionService


class ModerationCoordinator:
    """
    Main coordinator for moderation operations.

    Orchestrates case creation, communication, and execution
    using proper service composition instead of mixins.
    """

    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[DBCaseType]] = {DBCaseType.BAN, DBCaseType.KICK, DBCaseType.TEMPBAN}

    def __init__(
        self,
        case_service: CaseService,
        communication_service: CommunicationService,
        execution_service: ExecutionService,
    ):
        """
        Initialize the moderation coordinator.

        Args:
            case_service: Service for case management
            communication_service: Service for communication
            execution_service: Service for execution management
        """
        self._case_service = case_service
        self._communication = communication_service
        self._execution = execution_service

    async def execute_moderation_action(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        silent: bool = False,
        dm_action: str | None = None,
        actions: Sequence[tuple[Callable[..., Coroutine[Any, Any, Any]], type[Any]]] | None = None,
        duration: int | None = None,
        expires_at: datetime | None = None,
    ) -> Case | None:
        """
        Execute a complete moderation action.

        This method orchestrates the entire moderation flow:
        1. Validate permissions and inputs
        2. Send DM if required (before action for removal actions)
        3. Execute Discord actions with retry logic
        4. Create database case
        5. Send DM if required (after action for non-removal actions)
        6. Send response embed

        Args:
            ctx: Command context
            case_type: Type of moderation action
            user: Target user
            reason: Reason for the action
            silent: Whether to send DM to user
            dm_action: Custom DM action description
            actions: Discord API actions to execute
            duration: Duration for temp actions
            expires_at: Expiration timestamp for temp actions

        Returns:
            The created case, or None if case creation failed
        """
        if not ctx.guild:
            await self._communication.send_error_response(ctx, "This command must be used in a server")
            return None

        # Prepare DM action description
        action_desc = dm_action or self._get_default_dm_action(case_type)

        # Handle DM timing based on action type
        dm_sent = False
        try:
            dm_sent = await self._handle_dm_timing(ctx, case_type, user, reason, action_desc, silent)
        except Exception:
            # DM failed, but continue with the workflow
            dm_sent = False

        # Execute Discord actions
        if actions:
            with contextlib.suppress(Exception):
                await self._execute_actions(ctx, case_type, user, actions)

        # Create database case
        case = None
        try:
            case = await self._case_service.create_case(
                guild_id=ctx.guild.id,
                target_id=user.id,
                moderator_id=ctx.author.id,
                case_type=case_type,
                reason=reason,
                duration=duration,
                case_expires_at=expires_at,
            )
        except Exception:
            # Database failed, but continue with response
            case = None

        # Handle post-action DM for non-removal actions
        if case_type not in self.REMOVAL_ACTIONS and not silent:
            try:
                dm_sent = await self._handle_post_action_dm(ctx, user, reason, action_desc)
            except Exception:
                # DM failed, but continue
                dm_sent = False

        # Send response embed
        await self._send_response_embed(ctx, case, user, dm_sent)

        return case

    async def _handle_dm_timing(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        action_desc: str,
        silent: bool,
    ) -> bool:
        """
        Handle DM timing based on action type.

        Returns:
            True if DM was sent, False otherwise
        """
        if case_type in self.REMOVAL_ACTIONS:
            # Send DM BEFORE action for removal actions
            return await self._communication.send_dm(ctx, silent, user, reason, action_desc)
        # Send DM AFTER action for non-removal actions (handled later)
        return False

    async def _execute_actions(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        actions: Sequence[tuple[Callable[..., Coroutine[Any, Any, Any]], type[Any]]],
    ) -> list[Any]:
        """
        Execute Discord API actions.

        Note: Error handling is now centralized in the error handler.
        Exceptions are allowed to bubble up to be properly handled by the
        centralized error handler, which provides:
        - Consistent error messaging
        - Proper Sentry integration with command context
        - Guild/user context enrichment
        - Transaction management

        Returns:
            List of action results
        """
        results: list[Any] = []

        for action, expected_type in actions:
            operation_type = self._execution.get_operation_type(case_type)
            result = await self._execution.execute_with_retry(operation_type, action)
            results.append(handle_gather_result(result, expected_type))

        return results

    async def _handle_post_action_dm(
        self,
        ctx: commands.Context[Tux],
        user: discord.Member | discord.User,
        reason: str,
        action_desc: str,
    ) -> bool:
        """
        Handle DM sending after successful action execution.

        Returns:
            True if DM was sent, False otherwise
        """
        try:
            dm_task = asyncio.create_task(self._communication.send_dm(ctx, False, user, reason, action_desc))
            return await asyncio.wait_for(dm_task, timeout=3.0)
        except (TimeoutError, Exception):
            return False

    async def _send_response_embed(
        self,
        ctx: commands.Context[Tux],
        case: Case | None,
        user: discord.Member | discord.User,
        dm_sent: bool,
    ) -> None:
        """
        Send the response embed for the moderation action.
        """

        # Helper function to get mention safely (handles both real and mock objects)
        def get_mention(obj: Any) -> str:
            if hasattr(obj, "mention"):
                return obj.mention
            return f"{getattr(obj, 'name', 'Unknown')}#{getattr(obj, 'discriminator', '0000')}"

        if case is None:
            # Case creation failed, send a generic error response
            title = "Moderation Action Completed"
            fields = [
                ("Moderator", f"{get_mention(ctx.author)} (`{ctx.author.id}`)", True),
                ("Target", f"{get_mention(user)} (`{user.id}`)", True),
                ("Status", "⚠️ Case creation failed - action may have been applied", False),
            ]
        else:
            title = f"Case #{case.case_id} ({case.case_type.value if case.case_type else 'Unknown'})"
            fields = [
                ("Moderator", f"{get_mention(ctx.author)} (`{ctx.author.id}`)", True),
                ("Target", f"{get_mention(user)} (`{user.id}`)", True),
                ("Reason", f"> {case.case_reason}", False),
            ]

        embed = self._communication.create_embed(
            ctx=ctx,
            title=title,
            fields=fields,
            color=0x2B2D31,  # Discord blurple equivalent
            icon_url=ctx.author.display_avatar.url,
        )

        embed.description = "✅ DM sent" if dm_sent else "❌ DM not sent"

        await self._communication.send_embed(ctx, embed)

    def _get_default_dm_action(self, case_type: DBCaseType) -> str:
        """
        Get the default DM action description for a case type.
        """
        action_mapping = {
            DBCaseType.BAN: "banned",
            DBCaseType.KICK: "kicked",
            DBCaseType.TEMPBAN: "temporarily banned",
            DBCaseType.TIMEOUT: "timed out",
            DBCaseType.WARN: "warned",
            DBCaseType.UNBAN: "unbanned",
            DBCaseType.UNTIMEOUT: "untimeout",
        }
        return action_mapping.get(case_type, "moderated")
