"""
Case execution for moderation actions.

Handles the core logic of executing moderation actions, creating cases, and coordinating DMs.
"""

import asyncio
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tux.database.controllers import DatabaseCoordinator

import discord
from discord.ext import commands
from loguru import logger

from tux.core.types import Tux
from tux.database.models import Case as DBCase
from tux.database.models import CaseType as DBCaseType
from tux.services.moderation.retry_handler import retry_handler
from tux.shared.exceptions import handle_gather_result


class CaseExecutor:
    """
    Handles the execution of moderation actions and case creation.

    This mixin provides functionality to:
    - Execute moderation actions with proper sequencing
    - Handle DM timing (before/after actions)
    - Create database cases for audit trails
    - Coordinate multiple action steps
    - Implement retry logic and circuit breaker patterns
    """

    if TYPE_CHECKING:
        db: "DatabaseCoordinator"

    # Mixin attributes (provided by composition) - overridden by BaseCog property

    def _get_operation_type(self, case_type: DBCaseType) -> str:
        """
        Get the operation type for retry handler based on case type.

        Parameters
        ----------
        case_type : DBCaseType
            The type of moderation case

        Returns
        -------
        str
            Operation type for retry configuration
        """
        # Map case types to operation types for retry handling
        operation_mapping = {
            DBCaseType.BAN: "ban_kick",
            DBCaseType.KICK: "ban_kick",
            DBCaseType.TEMPBAN: "ban_kick",
            DBCaseType.TIMEOUT: "timeout",
            DBCaseType.UNBAN: "ban_kick",
            DBCaseType.WARN: "messages",
        }

        return operation_mapping.get(case_type, "messages")  # Default to messages

    async def _dummy_action(self) -> None:
        """
        Dummy coroutine for moderation actions that only create a case without performing Discord API actions.

        Used by commands like warn, pollban, snippetban etc. that only need case creation.
        """
        return

    async def execute_mod_action(  # noqa: PLR0912,PLR0915
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        silent: bool,
        dm_action: str,
        actions: Sequence[tuple[Any, type[Any]]] = (),
        duration: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:  # sourcery skip: low-code-quality
        """
        Execute a moderation action with case creation, DM sending, and additional actions.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        case_type : CaseType
            The type of case to create.
        user : Union[discord.Member, discord.User]
            The target user of the moderation action.
        reason : str
            The reason for the moderation action.
        silent : bool
            Whether to send a DM to the user.
        dm_action : str
            The action description for the DM.
        actions : Sequence[tuple[Any, type[R]]]
            Additional actions to execute and their expected return types.
        duration : Optional[str]
            The duration of the action, if applicable (for display/logging).
        expires_at : Optional[datetime]
            The specific expiration time, if applicable.
        """

        assert ctx.guild

        # 🎯 PHASE 4: DM TIMING - BEST PRACTICE FOR USER NOTIFICATION
        dm_sent = False

        if not silent:
            if case_type in getattr(self, "REMOVAL_ACTIONS", set()):  # type: ignore
                # 🚨 REMOVAL ACTIONS: Attempt DM BEFORE action (best practice for user notification)
                try:
                    logger.info(f"Attempting DM to {user} before {case_type}")
                    dm_sent = await asyncio.wait_for(self.send_dm(ctx, silent, user, reason, dm_action), timeout=3.0)  # type: ignore
                    logger.info(f"DM {'sent successfully' if dm_sent else 'failed'} to {user} before {case_type}")
                except TimeoutError:
                    logger.warning(f"DM to {user} timed out before {case_type} - proceeding with action")
                    dm_sent = False
                except Exception as e:
                    logger.warning(f"DM to {user} failed before {case_type}: {e} - proceeding with action")
                    dm_sent = False
            else:
                # ✅ NON-REMOVAL ACTIONS: DM after action is fine
                # We'll handle DM in post-action phase
                pass

        # 🎯 PHASE 5: ACTION EXECUTION WITH COMPREHENSIVE ERROR HANDLING
        action_results: list[Any] = []

        for i, (action, expected_type) in enumerate(actions):
            try:
                logger.info(f"Executing action {i + 1}/{len(actions)} on {user}")

                # Use retry handler with circuit breaker for Discord API calls
                operation_type = self._get_operation_type(case_type)
                result = await retry_handler.execute_with_retry(operation_type, action)

                action_results.append(handle_gather_result(result, expected_type))
                logger.info(f"Action {i + 1} completed successfully on {user}")

            except discord.Forbidden as e:
                # Bot lacks permission
                logger.error(f"Permission denied executing action on {user}: {e}")
                await self.send_error_response(ctx, f"I don't have permission to perform this action. Missing: {e}")  # type: ignore
                raise

            except discord.NotFound as e:
                # User/channel/guild not found
                logger.error(f"Resource not found while executing action on {user}: {e}")
                await self.send_error_response(ctx, "Could not find the target user or channel.")  # type: ignore
                raise

            except discord.HTTPException as e:
                if e.status == 429:
                    # Rate limited (retry handler should have handled this)
                    logger.error(f"Rate limit error despite retry handler: {e}")
                    await self.send_error_response(ctx, "I'm being rate limited. Please try again in a moment.")  # type: ignore
                    raise
                if e.status >= 500:
                    # Discord server error (retry handler should have handled this)
                    logger.error(f"Discord server error despite retries: {e}")
                    await self.send_error_response(ctx, "Discord is experiencing issues. Please try again later.")  # type: ignore
                    raise
                # Other HTTP error
                logger.error(f"HTTP error executing action on {user}: {e}")
                await self.send_error_response(ctx, f"Failed to execute action: {e}")  # type: ignore
                raise

            except Exception as e:
                logger.error(f"Unexpected error executing action on {user}: {e}")
                await self.send_error_response(ctx, f"An unexpected error occurred: {type(e).__name__}")  # type: ignore
                raise

        # 📝 PHASE 6: POST-ACTION DM HANDLING
        if case_type not in getattr(self, "REMOVAL_ACTIONS", set()) and not silent:  # type: ignore
            # ✅ NON-REMOVAL ACTIONS: Send DM after successful action
            try:
                logger.info(f"Attempting DM to {user} after {case_type}")
                dm_task: asyncio.Task[bool] = self.send_dm(ctx, silent, user, reason, dm_action)  # type: ignore
                dm_result: bool = await asyncio.wait_for(dm_task, timeout=3.0)  # type: ignore
                dm_sent = self._handle_dm_result(user, dm_result)  # type: ignore
                logger.info(f"Post-action DM {'sent successfully' if dm_sent else 'failed'} to {user}")
            except TimeoutError:
                logger.warning(f"Post-action DM to {user} timed out")
                dm_sent = False
            except Exception as e:
                logger.warning(f"Post-action DM to {user} failed: {e}")
                dm_sent = False

        # 💾 PHASE 7: DATABASE & AUDIT LOGGING
        case_result = None
        db_transaction_active = False

        try:
            # Start transaction for atomic operation
            db_transaction_active = True
            logger.info(f"Creating database case for {case_type} on {user}")

            assert self.db is not None, "Database coordinator not available"  # type: ignore
            case_result: DBCase | None = await self.db.case.insert_case(  # type: ignore
                guild_id=ctx.guild.id,
                case_user_id=user.id,
                case_moderator_id=ctx.author.id,
                case_type=case_type,
                case_reason=reason,
                case_expires_at=expires_at,
            )

            logger.info(
                f"Successfully created case #{case_result.case_number if case_result else 'unknown'} for {user}",  # type: ignore
            )
            db_transaction_active = False  # Transaction completed successfully

        except Exception as e:
            logger.error(f"Failed to create case for {user}: {e}")
            # 🚨 CRITICAL: If database fails but action succeeded, we have data inconsistency
            if db_transaction_active:
                logger.critical(
                    f"Database transaction failed after successful {case_type} action on {user} - MANUAL REVIEW REQUIRED",
                )
                # In a real system, you'd want to:
                # 1. Log this for manual review
                # 2. Send alert to administrators
                # 3. Possibly attempt rollback of the Discord action (if possible)
                # 4. Flag the case for manual audit trail creation
            case_result = None

        # Handle case response
        await self.handle_case_response(  # type: ignore
            ctx,
            case_type,
            case_result.case_number if case_result else None,  # type: ignore
            reason,
            user,
            dm_sent,
            duration,
        )
