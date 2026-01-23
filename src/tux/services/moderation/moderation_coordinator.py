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
        """
        Initialize the moderation coordinator.

        Parameters
        ----------
        case_service : CaseService
            Service for case management.
        communication_service : CommunicationService
            Service for communication.
        execution_service : ExecutionService
            Service for execution management.
        """
        self._case_service = case_service
        self._communication = communication_service
        self._execution = execution_service

    async def execute_moderation_action(  # noqa: PLR0912, PLR0915
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
    ) -> Case | None:  # sourcery skip: low-code-quality
        """
        Execute a complete moderation action.

        This method orchestrates the entire moderation flow:
        1. Validate permissions and inputs
        2. Send DM if required (before action for removal actions)
        3. Execute Discord actions with retry logic
        4. Create database case
        5. Send DM if required (after action for non-removal actions)
        6. Send response embed to the moderator
        7. Send response embed to the log channel
        8. Update the case audit log message ID

        Parameters
        ----------
        ctx : commands.Context[Tux]
            Command context.
        case_type : DBCaseType
            Type of moderation action.
        user : discord.Member | discord.User
            Target user.
        reason : str
            Reason for the action.
        silent : bool, optional
            Whether to send DM to user, by default False.
        dm_action : str | None, optional
            Custom DM action description, by default None.
        actions : Sequence[tuple[Callable[..., Coroutine[Any, Any, Any]], type[Any]]] | None, optional
            Discord API actions to execute, by default None.
        duration : int | None, optional
            Duration for temp actions, by default None.
        expires_at : datetime | None, optional
            Expiration timestamp for temp actions, by default None.
        **extra_case_data : Any
            Additional case data fields.

        Returns
        -------
        Case | None
            The created case, or None if case creation failed.
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

        # Prepare DM action description
        action_desc = dm_action or self._get_default_dm_action(case_type)
        logger.trace(f"DM action description: {action_desc}, silent: {silent}")

        # Handle DM timing based on action type
        dm_sent = False
        try:
            logger.trace(f"Handling DM timing for {case_type.value}")
            dm_sent = await self._handle_dm_timing(
                ctx,
                case_type,
                user,
                reason,
                action_desc,
                silent,
            )
            logger.trace(f"DM sent status (pre-action): {dm_sent}")
        except Exception as e:
            # DM failed, but continue with the workflow
            logger.warning(f"Failed to send pre-action DM to user {user.id}: {e}")
            dm_sent = False

        # Prepare case data (can be done in parallel with Discord actions)
        case_expires_at = expires_at
        if duration is not None and expires_at is None:
            case_expires_at = datetime.now(UTC) + timedelta(seconds=duration)
            logger.debug(
                f"Converted duration {duration}s → expires_at {case_expires_at}",
            )
        elif expires_at is not None:
            logger.debug(f"Using provided expires_at: {expires_at}")
        else:
            logger.trace("No expiration set (permanent action)")

        # Build kwargs for optional case fields
        case_kwargs = {**extra_case_data}
        if case_expires_at is not None:
            case_kwargs["case_expires_at"] = case_expires_at

        # Execute Discord actions and create case in parallel (they're independent)
        case = None

        if actions:
            logger.trace(
                f"Executing {len(actions)} Discord actions for {case_type.value}",
            )
            # Prepare case creation task (can run in parallel)
            case_task = asyncio.create_task(
                self._create_case_async(
                    ctx,
                    case_type,
                    user,
                    reason,
                    case_kwargs,
                ),
            )

            # Execute Discord actions
            try:
                await self._execute_actions(ctx, case_type, user, actions)
                logger.success(
                    f"Successfully executed Discord actions for {case_type.value}",
                )
            except Exception as e:
                logger.error(
                    f"Failed to execute Discord actions for {case_type.value}: {e}",
                    exc_info=True,
                )
                case_task.cancel()
                raise

            # Wait for case creation to complete
            try:
                case = await case_task
            except Exception as e:
                logger.error(
                    f"Failed to create case for {case_type.value} on user {user.id}: {e!r}",
                    exc_info=True,
                )
                case = None
        else:
            # No Discord actions, just create case
            try:
                case = await self._create_case_async(
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
                case = None

        # Handle post-action DM for non-removal actions
        if case_type not in self.REMOVAL_ACTIONS and not silent:
            try:
                logger.trace(f"Sending post-action DM for {case_type.value}")
                dm_sent = await self._handle_post_action_dm(
                    ctx,
                    user,
                    reason,
                    action_desc,
                )
                logger.trace(f"DM sent status (post-action): {dm_sent}")
            except Exception as e:
                # DM failed, but continue
                logger.warning(f"Failed to send post-action DM to user {user.id}: {e}")
                dm_sent = False

        # Send response embed and mod log embed in parallel (they're independent)
        logger.trace(
            f"Sending response embed, case={'None' if case is None else case.id}, dm_sent={dm_sent}",
        )
        response_task = asyncio.create_task(
            self._send_response_embed(ctx, case, user, dm_sent),
        )

        mod_log_message = None
        if case is not None:
            logger.trace(
                f"Sending response embed to mod log for case #{case.case_number}",
            )
            mod_log_task = asyncio.create_task(
                self._send_mod_log_embed(ctx, case, user, dm_sent),
            )

            # Wait for both to complete, capturing exceptions
            response_result, mod_log_result = await asyncio.gather(
                response_task,
                mod_log_task,
                return_exceptions=True,
            )

            # Log any exceptions from response embed
            if isinstance(response_result, Exception):
                logger.error(
                    f"Failed to send response embed for {case_type.value}: {response_result}",
                    exc_info=response_result,
                )

            # Log any exceptions from mod log embed
            if isinstance(mod_log_result, Exception):
                logger.error(
                    f"Failed to send mod log embed for case #{case.case_number}: {mod_log_result}",
                    exc_info=mod_log_result,
                )
                mod_log_message = None
            else:
                mod_log_message = mod_log_result

            # Update case with mod log message ID only if mod log send succeeded
            if (
                mod_log_message is not None
                and not isinstance(mod_log_message, Exception)
                and case.id is not None
            ):
                # Type narrowing: mod_log_message is discord.Message | None at this point
                # After checking not None and not Exception, it must be discord.Message
                # Use getattr for safety with mocks in tests
                message_id: int | None = getattr(mod_log_message, "id", None)
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
        else:
            # Wait for response embed only
            try:
                await response_task
            except Exception as e:
                logger.error(
                    f"Failed to send response embed for {case_type.value}: {e}",
                )

        logger.success(
            f"Completed moderation action {case_type.value} on user {user.id}",
        )
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

        Returns
        -------
            True if DM was sent, False otherwise
        """
        if case_type in self.REMOVAL_ACTIONS:
            # Send DM BEFORE action for removal actions
            return await self._communication.send_dm(
                ctx,
                silent,
                user,
                reason,
                action_desc,
            )
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

        Returns
        -------
            List of action results
        """
        results: list[Any] = []

        for idx, action_tuple in enumerate(actions, 1):
            # Extract action from tuple (action, expected_type)
            action = action_tuple[0]
            operation_type = self._execution.get_operation_type(case_type)
            logger.trace(
                f"Executing action {idx}/{len(actions)} for {case_type.value} (operation: {operation_type})",
            )
            try:
                result = await self._execution.execute_with_retry(
                    operation_type,
                    action,
                )
                results.append(result)
                logger.trace(f"Action {idx}/{len(actions)} completed successfully")
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
        """
        Handle DM sending after successful action execution.

        Returns
        -------
            True if DM was sent, False otherwise
        """
        try:
            result = await asyncio.wait_for(
                self._communication.send_dm(ctx, False, user, reason, action_desc),
                timeout=15.0,
            )
        except TimeoutError:
            logger.warning(
                f"Post-action DM to user {user.id} timed out after 15 seconds",
            )
            return False
        except asyncio.CancelledError:
            logger.warning(
                f"Post-action DM to user {user.id} was cancelled",
            )
            return False
        except Exception as e:
            logger.warning(f"Failed to send post-action DM to user {user.id}: {e}")
            return False
        else:
            logger.trace(f"Post-action DM sent to user {user.id}: {result}")
            return result

    async def _create_case_async(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        user: discord.Member | discord.User,
        reason: str,
        case_kwargs: dict[str, Any],
    ) -> Case:
        """
        Create a case asynchronously (helper for parallel execution).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            Command context.
        case_type : DBCaseType
            Type of moderation action.
        user : discord.Member | discord.User
            Target user.
        reason : str
            Reason for the action.
        case_kwargs : dict[str, Any]
            Additional case data.

        Returns
        -------
        Case
            The created case.
        """
        logger.trace(
            f"Creating case: type={case_type.value}, user={user.id}, moderator={ctx.author.id}, "
            f"guild={ctx.guild.id if ctx.guild else None}, case_kwargs={case_kwargs!r}",
        )
        case = await self._case_service.create_case(
            guild_id=ctx.guild.id if ctx.guild else 0,
            user_id=user.id,
            moderator_id=ctx.author.id,
            case_type=case_type,
            reason=reason,
            **case_kwargs,
        )
        logger.success(
            f"Successfully created case #{case.case_number} (ID: {case.id}) for {case_type.value}",
        )
        return case

    def _create_base_embed(
        self,
        case: Case | None,
        user: discord.Member | discord.User,
        ctx: commands.Context[Tux],
        dm_sent: bool,
    ) -> discord.Embed:
        """
        Create base embed for moderation action (shared between response and mod log).

        Parameters
        ----------
        case : Case | None
            The moderation case, or None if creation failed.
        user : discord.Member | discord.User
            Target user.
        ctx : commands.Context[Tux]
            Command context.
        dm_sent : bool
            Whether DM was sent.

        Returns
        -------
        discord.Embed
            Base embed with common fields.
        """
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

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.ACTIVE_CASE,
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
        logger.trace(
            f"Preparing response embed, case={'present' if case else 'None'}, dm_sent={dm_sent}",
        )

        embed = self._create_base_embed(case, user, ctx, dm_sent)
        await self._communication.send_embed(ctx, embed)
        logger.trace("Response embed sent successfully")

    async def _send_mod_log_embed(
        self,
        ctx: commands.Context[Tux],
        case: Case,
        user: discord.Member | discord.User,
        dm_sent: bool,
    ) -> discord.Message | None:
        """Send the response embed to the mod log channel."""
        logger.trace(f"Preparing mod log embed for case #{case.case_number}")

        # Create base embed and clone for mod log
        embed = self._create_base_embed(case, user, ctx, dm_sent)

        # Add expiration field if applicable
        if case.case_expires_at:
            # Ensure UTC-aware datetime before getting timestamp
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

        # Set embed timestamp to case creation time
        # Ensure UTC-aware datetime (database stores as UTC but returns naive)
        if case.created_at:
            if case.created_at.tzinfo is None:
                # Naive datetime from database - treat as UTC
                embed.timestamp = case.created_at.replace(tzinfo=UTC)
            else:
                embed.timestamp = case.created_at

        # Send to mod log channel
        return await self._communication.send_mod_log_embed(ctx, embed)

    def _get_default_dm_action(self, case_type: DBCaseType) -> str:
        """Get the default DM action description for a case type.

        Returns
        -------
        str
            Default action description for the case type.
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
