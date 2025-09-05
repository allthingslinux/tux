"""
Complete moderation service integrating all components.

This service orchestrates the entire moderation flow with proper error handling,
retry logic, circuit breakers, monitoring, and audit trails.
"""

import asyncio
import time
import traceback
from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.core.types import Tux
from tux.database.controllers import DatabaseCoordinator
from tux.database.models import CaseType as DBCaseType
from tux.services.moderation.case_executor import CaseExecutor
from tux.services.moderation.case_response_handler import CaseResponseHandler
from tux.services.moderation.condition_checker import ConditionChecker
from tux.services.moderation.dm_handler import DMHandler
from tux.services.moderation.embed_manager import EmbedManager
from tux.services.moderation.lock_manager import LockManager
from tux.services.moderation.monitoring import ModerationAuditEvent, moderation_monitor
from tux.services.moderation.retry_handler import retry_handler
from tux.services.moderation.status_checker import StatusChecker
from tux.services.moderation.timeout_handler import timeout_handler
from tux.shared.exceptions import handle_gather_result


class ModerationError(Exception):
    """Custom exception for moderation operation failures."""


class ModerationService(
    CaseExecutor,
    CaseResponseHandler,
    ConditionChecker,
    DMHandler,
    EmbedManager,
    LockManager,
    StatusChecker,
):
    """
    Complete moderation service integrating all moderation components.

    This service provides a production-ready moderation system with:
    - Comprehensive error handling and recovery
    - Retry logic with circuit breakers
    - Concurrent operation handling
    - Performance monitoring and audit trails
    - Timeout handling with graceful degradation
    - Proper transaction management
    """

    def __init__(self, bot: Tux, db_coordinator: DatabaseCoordinator | None = None):
        # Initialize all parent classes
        CaseExecutor.__init__(self)
        CaseResponseHandler.__init__(self)
        ConditionChecker.__init__(self)
        DMHandler.__init__(self)
        EmbedManager.__init__(self)
        LockManager.__init__(self)
        StatusChecker.__init__(self)

        self.bot = bot
        # Use provided database coordinator or get it from bot
        if db_coordinator is not None:
            self.db = db_coordinator  # type: ignore
        else:
            # Fallback - try to get from bot (though this shouldn't be needed)
            self.db = getattr(bot, "db", None)  # type: ignore
            if self.db is None:  # type: ignore
                logger.warning("Database coordinator not available in ModerationService")

    async def execute_moderation_action(  # noqa: PLR0912, PLR0915
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
        Execute a complete moderation action with all safety measures.

        This is the main entry point for all moderation operations and includes:
        - Phase 1: Initial validation
        - Phase 2: Permission & authorization checks
        - Phase 3: Hierarchy & role validation
        - Phase 4: Pre-action preparation (locks, DM timing)
        - Phase 5: Action execution with retry logic
        - Phase 6: Post-action processing (responses, DMs)
        - Phase 7: Database & audit logging

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
            DM action description
        actions : list[tuple[Any, type[Any]]]
            Discord API actions to execute
        duration : str | None
            Duration string for display
        expires_at : int | None
            Expiration timestamp
        """
        actions = actions or []

        # 🔍 PHASE 1: INITIAL VALIDATION
        operation_type = self._get_operation_type(case_type)
        start_time = moderation_monitor.start_operation(operation_type)

        audit_event = ModerationAuditEvent(
            timestamp=start_time,
            operation_type=operation_type,
            user_id=user.id,
            moderator_id=ctx.author.id,
            guild_id=ctx.guild.id if ctx.guild else 0,
            case_type=case_type.value,
            success=False,
            response_time=0.0,
            dm_sent=False,
            case_created=False,
        )

        try:
            # Validate basic requirements
            if not ctx.guild:
                error_msg = "Moderation actions must be performed in a guild"

                def _raise_validation_error():
                    raise ModerationError(error_msg)  # noqa: TRY301

                _raise_validation_error()

            if not dm_action:
                dm_action = case_type.value.lower()

            # 🔐 PHASE 2: PERMISSION & AUTHORIZATION CHECKS
            logger.info(f"Starting moderation action: {case_type} on {user}")

            # Check bot permissions first (critical)
            bot_has_perms, bot_error = await self.check_bot_permissions(ctx, case_type.value.lower())
            if not bot_has_perms:
                await self.send_error_response(ctx, bot_error or "Unknown permission error")
                audit_event.error_message = bot_error
                return

            # ⚖️ PHASE 3: HIERARCHY & ROLE VALIDATION
            conditions_met = await self.check_conditions(ctx, user, ctx.author, case_type.value.lower())
            if not conditions_met:
                audit_event.error_message = "Authorization failed"
                return

            # 🔒 PHASE 4: PRE-ACTION PREPARATION
            # Get user lock and handle queuing
            user_lock = await self.get_user_lock(user.id)

            async with user_lock:
                logger.info(f"Acquired lock for user {user.id}")

                # Execute the moderation action with full error handling
                await self._execute_with_full_protection(
                    ctx,
                    case_type,
                    user,
                    reason,
                    silent,
                    dm_action,
                    actions,
                    duration,
                    expires_at,
                    audit_event,
                )

                logger.info(f"Released lock for user {user.id}")

            # Mark operation as successful
            audit_event.success = True
            moderation_monitor.end_operation(operation_type, start_time, True)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Moderation action failed: {error_msg}")

            # Record failure
            audit_event.error_message = error_msg
            moderation_monitor.end_operation(operation_type, start_time, False, error_msg)

            # Send user-friendly error message
            try:
                # Check specific exception types first (including in exception chain)
                def get_original_exception(exc: BaseException) -> BaseException:
                    """Get the original exception from a chain of wrapped exceptions."""
                    if isinstance(exc, discord.NotFound):
                        return exc
                    if isinstance(exc, discord.Forbidden):
                        return exc
                    if isinstance(exc, discord.HTTPException):
                        return exc
                    # Check exception chain
                    if hasattr(exc, "__cause__") and exc.__cause__:
                        return get_original_exception(exc.__cause__)
                    if hasattr(exc, "__context__") and exc.__context__:
                        return get_original_exception(exc.__context__)
                    return exc

                original_exception = get_original_exception(e)

                if isinstance(original_exception, discord.NotFound):
                    await self.send_error_response(
                        ctx,
                        "Could not find the user or target. They may have left the server.",
                    )
                elif isinstance(original_exception, discord.Forbidden):
                    await self.send_error_response(ctx, "I don't have permission to perform this action.")
                elif isinstance(original_exception, discord.HTTPException):
                    if original_exception.status == 429:
                        await self.send_error_response(
                            ctx,
                            "I'm being rate limited. Please wait a moment and try again.",
                        )
                    else:
                        await self.send_error_response(ctx, "A Discord error occurred. Please try again.")
                elif isinstance(original_exception, asyncio.TimeoutError) or "timeout" in error_msg.lower():
                    await self.send_error_response(ctx, "The operation timed out. Please try again.")
                elif "permission" in error_msg.lower():
                    await self.send_error_response(ctx, "I don't have permission to perform this action.")
                elif "rate limit" in error_msg.lower():
                    await self.send_error_response(ctx, "I'm being rate limited. Please wait a moment and try again.")
                else:
                    # Generic fallback with better formatting
                    error_type = type(e).__name__
                    if error_type == "ModerationError":
                        # Check if we can identify the underlying Discord error from the message
                        if "NotFound" in error_msg:
                            await self.send_error_response(
                                ctx,
                                "Could not find the user or target. They may have left the server.",
                            )
                        elif "Forbidden" in error_msg:
                            await self.send_error_response(ctx, "I don't have permission to perform this action.")
                        else:
                            await self.send_error_response(ctx, "The moderation action could not be completed.")
                    else:
                        await self.send_error_response(ctx, f"An unexpected error occurred: {error_type}")
            except Exception as send_error:
                logger.error(f"Failed to send error response: {send_error}")

        finally:
            # Record audit event
            audit_event.response_time = time.time() - start_time
            moderation_monitor.record_audit_event(audit_event)

    async def _execute_with_full_protection(  # noqa: PLR0915
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        silent: bool,
        dm_action: str,
        actions: list[tuple[Any, type[Any]]],
        duration: str | None,
        expires_at: int | None,
        audit_event: ModerationAuditEvent,
    ) -> None:  # sourcery skip: low-code-quality
        """
        Execute moderation action with full protection layers.

        This method implements the core execution logic with all safety measures.
        """
        operation_type = self._get_operation_type(case_type)

        # 🎯 PHASE 4: DM TIMING
        dm_sent = False

        if not silent and case_type in getattr(self, "REMOVAL_ACTIONS", set()):  # type: ignore
            # 🚨 REMOVAL ACTIONS: Attempt DM BEFORE action
            try:
                dm_result = await timeout_handler.execute_dm_with_timeout(
                    operation_type,
                    self.send_dm,
                    ctx,
                    silent,
                    user,
                    reason,
                    dm_action,
                )
                dm_sent = dm_result is not None
                logger.info(f"DM {'sent successfully' if dm_sent else 'failed'} to {user} before {case_type}")
            except Exception as e:
                logger.warning(f"DM to {user} failed before {case_type}: {e}")
                dm_sent = False

        # 🎯 PHASE 5: ACTION EXECUTION WITH RETRY LOGIC
        action_results = []

        for i, (action, expected_type) in enumerate(actions):
            try:
                logger.info(f"Executing action {i + 1}/{len(actions)} on {user}")

                # Use retry handler with circuit breaker
                result = await retry_handler.execute_with_retry(operation_type, action)
                action_results.append(handle_gather_result(result, expected_type))  # type: ignore

                logger.info(f"Action {i + 1} completed successfully on {user}")

            except Exception as e:
                logger.error(f"Action execution failed on {user}: {e}")
                error_msg = f"Failed to execute moderation action on {user}: {type(e).__name__}"
                raise ModerationError(error_msg) from e

        # 📝 PHASE 6: POST-ACTION DM HANDLING
        if case_type not in getattr(self, "REMOVAL_ACTIONS", set()) and not silent:  # type: ignore
            try:
                dm_result = await timeout_handler.execute_dm_with_timeout(
                    operation_type,
                    self.send_dm,
                    ctx,
                    silent,
                    user,
                    reason,
                    dm_action,
                )
                dm_sent = dm_result is not None
                logger.info(f"Post-action DM {'sent successfully' if dm_sent else 'failed'} to {user}")
            except Exception as e:
                logger.warning(f"Post-action DM to {user} failed: {e}")
                dm_sent = False

        # 💾 PHASE 7: DATABASE & AUDIT LOGGING
        case_result = None

        try:
            # Use timeout handler for database operations
            logger.info(
                f"About to call insert_case with guild_id={ctx.guild.id if ctx.guild else 0}, user_id={user.id}",
            )
            if not self.db:
                msg = "Database not available"
                raise RuntimeError(msg)  # noqa: TRY301

            case_result = await timeout_handler.execute_database_with_timeout(
                operation_type,
                self.db.case.insert_case,
                guild_id=ctx.guild.id if ctx.guild else 0,
                case_user_id=user.id,
                case_moderator_id=ctx.author.id if ctx.author else 0,
                case_type=case_type,
                case_reason=reason,
                case_expires_at=expires_at,
            )
            logger.info(f"Case creation result: {case_result}")

            logger.info(
                f"Successfully created case #{case_result.case_number if case_result else 'unknown'} for {user}",
            )

            # Update audit event
            audit_event.dm_sent = dm_sent
            audit_event.case_created = case_result is not None  # type: ignore
            audit_event.case_number = case_result.case_number if case_result else None

        except Exception as e:
            logger.critical(
                f"Database operation failed after successful {case_type} action on {user} - MANUAL REVIEW REQUIRED",
            )
            logger.error(f"Database error details: {type(e).__name__}: {e}")
            logger.error(f"Database error traceback: {traceback.format_exc()}")
            # In production, this would trigger alerts and manual review
            audit_event.error_message = f"Database failure: {e}"
            # NOTE: We don't re-raise here because the Discord action succeeded
            # The user should still get feedback about the successful moderation action

        # Send final response and get audit log message
        audit_log_message = await self.handle_case_response(
            ctx,
            case_type,
            case_result.case_number if case_result else None,
            reason,
            user,
            dm_sent,
            duration,
        )

        # Update case with audit log message ID if we have both case and message
        if case_result and audit_log_message:
            try:
                if not self.db:
                    msg = "Database not available"
                    raise RuntimeError(msg)  # noqa: TRY301

                await timeout_handler.execute_database_with_timeout(
                    operation_type,
                    self.db.case.update_audit_log_message_id,
                    case_result.case_id,
                    audit_log_message.id,  # type: ignore
                )
                logger.info(f"Updated case #{case_result.case_number} with audit log message ID {audit_log_message.id}")  # type: ignore
            except Exception as e:
                logger.warning(f"Failed to update case #{case_result.case_number} with audit log message ID: {e}")
                # Don't fail the entire operation for this

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status and health metrics."""
        return {
            "health": moderation_monitor.get_system_health(),
            "performance": moderation_monitor.get_performance_summary(),
            "errors": moderation_monitor.get_error_summary(),
            "circuit_breakers": {
                op_type: {"state": cb.get_state().value, "metrics": cb.get_metrics().__dict__}
                for op_type, cb in retry_handler.circuit_breakers.items()
            },
            "active_queues": {user_id: queue.qsize() for user_id, queue in self._user_queues.items()},
        }

    async def cleanup_old_data(self) -> None:
        """Clean up old monitoring data and reset counters."""
        moderation_monitor.clear_old_data()
        logger.info("Cleaned up old moderation monitoring data")


# Convenience function for easy use
async def moderate_user(
    service: ModerationService,
    ctx: commands.Context[Tux],
    case_type: DBCaseType,
    user: discord.Member | discord.User,
    reason: str,
    **kwargs: Any,
) -> None:
    """
    Convenience function to execute moderation actions.

    This provides a simple interface for moderation commands.
    """
    await service.execute_moderation_action(ctx=ctx, case_type=case_type, user=user, reason=reason, **kwargs)
