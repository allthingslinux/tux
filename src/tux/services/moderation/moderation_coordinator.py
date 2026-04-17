"""
Moderation coordinator service.

Orchestrates all moderation services and provides the main interface
for moderation operations, replacing the mixin-based approach.
"""

import asyncio
from collections.abc import Callable, Coroutine, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

import discord
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType
from tux.ui.embeds import EmbedCreator, EmbedType

from .case_service import CaseService
from .communication_service import CommunicationService
from .execution_service import ExecutionService


class _ActionFailedError(Exception):
    """Internal sentinel: Discord action failed, case voided/cancelled."""


class ModerationCoordinator:
    """
    Main coordinator for moderation operations.

    Orchestrates case creation, communication, and execution
    using proper service composition instead of mixins.
    """

    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[DBCaseType]] = {
        DBCaseType.BAN,
        DBCaseType.KICK,
        DBCaseType.TEMPBAN,
    }

    def __init__(
        self,
        case_service: CaseService,
        communication_service: CommunicationService,
        execution_service: ExecutionService,
    ):
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
        actions: Sequence[tuple[Callable[..., Coroutine[Any, Any, Any]], type[Any]]]
        | None = None,
        duration: int | None = None,
        expires_at: datetime | None = None,
        **extra_case_data: Any,
    ) -> Case | None:
        """Execute a complete moderation action.

        Orchestrates: DM → Discord actions → case creation → response embeds → mod log.
        """
        logger.info(
            f"Executing moderation action: {case_type.value} on user {user.id} by {ctx.author.id} in guild {ctx.guild.id if ctx.guild else 'None'}",
        )

        if not ctx.guild:
            logger.warning("Moderation action attempted outside of guild context")
            await self._communication.send_error_response(
                ctx,
                "This command must be used in a server",
            )
            return None

        action_desc = dm_action or self._get_default_dm_action(case_type)
        case_kwargs = self._build_case_kwargs(extra_case_data, duration, expires_at)

        # Pre-action DM for removal actions (must happen before user is removed)
        dm_sent = await self._send_pre_action_dm(
            ctx,
            case_type,
            user,
            reason,
            action_desc,
            silent,
        )

        # Execute action + create case
        if actions:
            try:
                case = await self._execute_with_actions(
                    ctx,
                    case_type,
                    user,
                    reason,
                    case_kwargs,
                    actions,
                )
            except _ActionFailedError:
                return None
        else:
            case = await self._execute_without_actions(
                ctx,
                case_type,
                user,
                reason,
                case_kwargs,
            )

        # Post-action DM for non-removal actions (e.g. WARN)
        if case_type not in self.REMOVAL_ACTIONS and not silent:
            dm_sent = await self._handle_post_action_dm(ctx, user, reason, action_desc)

        # Send response + mod log embeds
        await self._send_embeds_and_update_log(ctx, case_type, case, user, dm_sent)

        logger.success(
            f"Completed moderation action {case_type.value} on user {user.id}",
        )
        return case

    # ------------------------------------------------------------------
    # Step helpers
    # ------------------------------------------------------------------

    def _build_case_kwargs(
        self,
        extra_case_data: dict[str, Any],
        duration: int | None,
        expires_at: datetime | None,
    ) -> dict[str, Any]:
        """Build kwargs dict for case creation, converting duration to expires_at."""
        kwargs = {**extra_case_data}
        if duration is not None and expires_at is None:
            kwargs["case_expires_at"] = datetime.now(UTC) + timedelta(seconds=duration)
        elif expires_at is not None:
            kwargs["case_expires_at"] = expires_at
        return kwargs

    async def _send_pre_action_dm(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        action_desc: str,
        silent: bool,
    ) -> bool:
        """Send DM before action for removal actions (ban/kick/tempban)."""
        if case_type not in self.REMOVAL_ACTIONS:
            return False
        try:
            return await self._communication.send_dm(
                ctx,
                silent,
                user,
                reason,
                action_desc,
            )
        except Exception as e:  # Catch-all: DM failure must not block moderation
            logger.warning(f"Failed to send pre-action DM to user {user.id}: {e}")
            return False

    async def _execute_with_actions(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        case_kwargs: dict[str, Any],
        actions: Sequence[tuple[Callable[..., Coroutine[Any, Any, Any]], type[Any]]],
    ) -> Case | None:
        """Execute Discord actions and create case in parallel.

        Raises _ActionFailedError if the Discord action fails (case is voided/cancelled).
        Returns None if case creation fails (action succeeded, continue flow).
        """
        case_task = asyncio.create_task(
            self._create_case_async(ctx, case_type, user, reason, case_kwargs),
        )

        try:
            await self._execute_actions(ctx, case_type, user, actions)
        except (discord.NotFound, discord.Forbidden) as e:
            error_type = (
                "left guild"
                if isinstance(e, discord.NotFound)
                else "missing permissions"
            )
            logger.warning(f"User {user.id} {error_type} during {case_type.value}: {e}")
            await self._handle_failed_case_task(case_task, error_type, e)
            raise _ActionFailedError from e
        except Exception as e:
            logger.error(
                f"Failed to execute Discord actions for {case_type.value}: {e}",
                exc_info=True,
            )
            await self._handle_failed_case_task(case_task, "Discord action failed", e)
            raise

        try:
            return await case_task
        except Exception as e:
            logger.error(
                f"Failed to create case for {case_type.value} on user {user.id}: {e!r}",
                exc_info=True,
            )
            return None

    async def _execute_without_actions(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        case_kwargs: dict[str, Any],
    ) -> Case | None:
        """Create case without Discord actions (e.g. jail, note)."""
        try:
            return await self._create_case_async(
                ctx,
                case_type,
                user,
                reason,
                case_kwargs,
            )
        except Exception as e:
            logger.error(
                f"Failed to create case for {case_type.value} on user {user.id}: {e!r}",
                exc_info=True,
            )
            return None

    async def _handle_failed_case_task(
        self,
        case_task: asyncio.Task[Case],
        error_context: str,
        original_error: Exception,
    ) -> None:
        """Handle a case creation task when the Discord action failed.

        If the case was already created, void it to preserve audit trail.
        If still pending, cancel it.
        """
        if case_task.done():
            try:
                created_case = await case_task
                if created_case.id is not None:
                    error_msg = str(original_error)[:100]
                    try:
                        await self._case_service.void_case(
                            created_case.id,
                            failure_reason=f"{error_context}: {error_msg}",
                        )
                        logger.warning(
                            f"Voided case #{created_case.case_number} (ID: {created_case.id}) "
                            f"because {error_context}. Case preserved for audit trail.",
                        )
                    except Exception as void_error:
                        logger.error(
                            f"Failed to void case #{created_case.case_number}: {void_error}",
                            exc_info=True,
                        )
            except Exception:
                logger.debug("Case creation also failed (expected)")
        else:
            case_task.cancel()
            try:
                await case_task
            except asyncio.CancelledError:
                logger.trace("Case creation task cancelled successfully")

    async def _send_embeds_and_update_log(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        case: Case | None,
        user: discord.Member | discord.User,
        dm_sent: bool,
    ) -> None:
        """Send response embed and mod log embed, then update case with log message ID."""
        response_task = asyncio.create_task(
            self._send_response_embed(ctx, case, user, dm_sent),
        )

        if case is None:
            try:
                await response_task
            except Exception as e:
                logger.error(
                    f"Failed to send response embed for {case_type.value}: {e}",
                )
            return

        mod_log_task = asyncio.create_task(
            self._send_mod_log_embed(ctx, case, user, dm_sent),
        )
        response_result, mod_log_result = await asyncio.gather(
            response_task,
            mod_log_task,
            return_exceptions=True,
        )

        if isinstance(response_result, Exception):
            logger.error(
                f"Failed to send response embed for {case_type.value}: {response_result}",
                exc_info=response_result,
            )
        if isinstance(mod_log_result, Exception):
            logger.error(
                f"Failed to send mod log embed for case #{case.case_number}: {mod_log_result}",
                exc_info=mod_log_result,
            )
            return

        # Update case with mod log message ID
        if mod_log_result is not None and case.id is not None:
            message_id: int | None = getattr(mod_log_result, "id", None)
            if message_id is not None:
                try:
                    await self._case_service.update_mod_log_message_id(
                        case.id,
                        message_id,
                    )
                    logger.info(
                        f"Updated case #{case.case_number} with mod log message ID {message_id}",
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to update mod log message ID for case #{case.case_number}: {e}",
                    )

    # ------------------------------------------------------------------
    # Existing helpers (unchanged)
    # ------------------------------------------------------------------

    async def _handle_dm_timing(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        action_desc: str,
        silent: bool,
    ) -> bool:
        """Handle DM timing based on action type."""
        if case_type in self.REMOVAL_ACTIONS:
            return await self._communication.send_dm(
                ctx,
                silent,
                user,
                reason,
                action_desc,
            )
        return False

    async def _execute_actions(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        actions: Sequence[tuple[Callable[..., Coroutine[Any, Any, Any]], type[Any]]],
    ) -> list[Any]:
        """Execute Discord API actions with retry logic."""
        results: list[Any] = []
        for idx, (action, __) in enumerate(actions, 1):
            operation_type = self._execution.get_operation_type(case_type)
            try:
                result = await self._execution.execute_with_retry(
                    operation_type,
                    action,
                )
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Action {idx}/{len(actions)} failed for {case_type.value}: {e}",
                )
                raise
        return results

    async def _handle_post_action_dm(
        self,
        ctx: commands.Context[Tux],
        user: discord.Member | discord.User,
        reason: str,
        action_desc: str,
    ) -> bool:
        """Send DM after successful action execution."""
        try:
            return await asyncio.wait_for(
                self._communication.send_dm(ctx, False, user, reason, action_desc),
                timeout=15.0,
            )
        except TimeoutError:
            logger.warning(
                f"Post-action DM to user {user.id} timed out after 15 seconds",
            )
            return False
        except asyncio.CancelledError:
            logger.warning(f"Post-action DM to user {user.id} was cancelled")
            return False
        except Exception as e:  # Catch-all: DM failure must not block moderation
            logger.warning(f"Failed to send post-action DM to user {user.id}: {e}")
            return False

    async def _create_case_async(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        case_kwargs: dict[str, Any],
    ) -> Case:
        """Create a case asynchronously (helper for parallel execution)."""
        case = await self._case_service.create_case(
            guild_id=ctx.guild.id if ctx.guild else 0,
            user_id=user.id,
            moderator_id=ctx.author.id,
            case_type=case_type,
            reason=reason,
            **case_kwargs,
        )
        logger.success(
            f"Created case #{case.case_number} (ID: {case.id}) for {case_type.value}",
        )
        return case

    def _create_base_embed(
        self,
        case: Case | None,
        user: discord.Member | discord.User,
        ctx: commands.Context[Tux],
        dm_sent: bool,
    ) -> discord.Embed:
        """Create base embed for moderation action (shared between response and mod log)."""
        if case is None:
            title = "Moderation Action Completed"
            fields = [
                ("Moderator", f"{ctx.author.name}\n`{ctx.author.id}`", True),
                ("Target", f"{user.name}\n`{user.id}`", True),
                (
                    "Status",
                    "⚠️ Case creation failed - action may have been applied",
                    False,
                ),
            ]
        else:
            title = f"Case #{case.case_number} ({case.case_type.value if case.case_type else 'Unknown'})"
            fields = [
                ("Moderator", f"{ctx.author.name}\n`{ctx.author.id}`", True),
                ("Target", f"{user.name}\n`{user.id}`", True),
                ("Reason", f"> {case.case_reason}", False),
            ]

        embed_type = (
            EmbedType.ACTIVE_CASE
            if (case is None or case.case_status)
            else EmbedType.INACTIVE_CASE
        )
        embed = EmbedCreator.create_embed(
            embed_type=embed_type,
            description="✅ DM sent" if dm_sent else "❌ DM not sent",
            custom_author_text=title,
        )
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        return embed

    async def _send_response_embed(
        self,
        ctx: commands.Context[Tux],
        case: Case | None,
        user: discord.Member | discord.User,
        dm_sent: bool,
    ) -> None:
        """Send the response embed for the moderation action."""
        embed = self._create_base_embed(case, user, ctx, dm_sent)
        await self._communication.send_embed(ctx, embed)

    async def _send_mod_log_embed(
        self,
        ctx: commands.Context[Tux],
        case: Case,
        user: discord.Member | discord.User,
        dm_sent: bool,
    ) -> discord.Message | None:
        """Send the response embed to the mod log channel."""
        embed = self._create_base_embed(case, user, ctx, dm_sent)

        if case.case_expires_at:
            expires_at = (
                case.case_expires_at.replace(tzinfo=UTC)
                if case.case_expires_at.tzinfo is None
                else case.case_expires_at
            )
            embed.add_field(
                name="Expires",
                value=f"<t:{int(expires_at.timestamp())}:R>",
                inline=True,
            )

        if case.created_at:
            embed.timestamp = (
                case.created_at.replace(tzinfo=UTC)
                if case.created_at.tzinfo is None
                else case.created_at
            )

        return await self._communication.send_mod_log_embed(ctx, embed)

    def _get_default_dm_action(self, case_type: DBCaseType) -> str:
        """Get the default DM action description for a case type."""
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
