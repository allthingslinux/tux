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

        # Execute Discord actions
        if actions:
            logger.trace(
                f"Executing {len(actions)} Discord actions for {case_type.value}",
            )
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

        # Create database case
        case = None

        try:
            # Calculate case_expires_at from duration if needed
            # Duration is in seconds, convert to datetime
            logger.trace(
                f"Duration/expires_at conversion: duration={duration}, expires_at={expires_at}",
            )

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

            logger.trace(
                f"Creating case: type={case_type.value}, user={user.id}, moderator={ctx.author.id}, "
                f"guild={ctx.guild.id}, case_kwargs={case_kwargs!r}",
            )
            case = await self._case_service.create_case(
                guild_id=ctx.guild.id,
                user_id=user.id,
                moderator_id=ctx.author.id,
                case_type=case_type,
                reason=reason,
                **case_kwargs,  # All optional Case fields (expires_at, user_roles, metadata, etc.)
            )
            logger.success(
                f"Successfully created case #{case.case_number} (ID: {case.id}) for {case_type.value}",
            )

        except Exception as e:
            # Database failed, but continue with response
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

        # Send response embed to moderator
        logger.trace(
            f"Sending response embed, case={'None' if case is None else case.id}, dm_sent={dm_sent}",
        )
        await self._send_response_embed(ctx, case, user, dm_sent)

        # Send response embed to mod log channel and update case
        if case is not None:
            logger.trace(
                f"Sending response embed to mod log for case #{case.case_number}",
            )
            mod_log_message = await self._send_mod_log_embed(ctx, case, user, dm_sent)
            if mod_log_message:
                try:
                    if case.id is not None:
                        await self._case_service.update_mod_log_message_id(
                            case.id,
                            mod_log_message.id,
                        )
                        logger.info(
                            f"Updated case #{case.case_number} with mod log message ID {mod_log_message.id}",
                        )
                    else:
                        logger.error(
                            f"Cannot update mod log message ID: case.id is None for case #{case.case_number}",
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to update mod log message ID for case #{case.case_number}: {e}",
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

        for idx, (action, _expected_type) in enumerate(actions, 1):
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
            dm_task = asyncio.create_task(
                self._communication.send_dm(ctx, False, user, reason, action_desc),
            )
            result = await asyncio.wait_for(dm_task, timeout=15.0)
        except TimeoutError:
            logger.warning(
                f"Post-action DM to user {user.id} timed out after 3 seconds",
            )
            return False
        except Exception as e:
            logger.warning(f"Failed to send post-action DM to user {user.id}: {e}")
            return False
        else:
            logger.trace(f"Post-action DM sent to user {user.id}: {result}")
            return result

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

        # Helper function to get mention safely (handles both real and mock objects)
        def get_mention(obj: Any) -> str:  # type: ignore[reportUnusedFunction]
            """
            Get mention string for a user object safely.

            Parameters
            ----------
            obj : Any
                The user or member object.

            Returns
            -------
            str
                The mention string or fallback name#discriminator format.
            """
            if hasattr(obj, "mention"):
                return obj.mention
            return f"{getattr(obj, 'name', 'Unknown')}#{getattr(obj, 'discriminator', '0000')}"

        if case is None:
            # Case creation failed, send a generic error response
            logger.warning("Sending response embed without case (case creation failed)")
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
            logger.trace(
                f"Sending response embed for case #{case.case_number} (ID: {case.id})",
            )
            title = f"Case #{case.case_number} ({case.case_type.value if case.case_type else 'Unknown'})"
            fields = [
                ("Moderator", f"{ctx.author.name}\n`{ctx.author.id}`", True),
                ("Target", f"{user.name}\n`{user.id}`", True),
                ("Reason", f"> {case.case_reason}", False),
            ]

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.ACTIVE_CASE,
            # title=title,
            description="✅ DM sent" if dm_sent else "❌ DM not sent",
            custom_author_text=title,
        )

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

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

        # Create a copy of the embed for mod log with different footer
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.ACTIVE_CASE,
            description="✅ DM sent" if dm_sent else "❌ DM not sent",
            custom_author_text=f"Case #{case.case_number} ({case.case_type.value if case.case_type else 'Unknown'})",
        )

        # Add case-specific fields for mod log
        fields = [
            ("Moderator", f"{ctx.author.name}\n`{ctx.author.id}`", True),
            ("Target", f"{user.name}\n`{user.id}`", True),
            ("Reason", f"> {case.case_reason}", False),
        ]

        if case.case_expires_at:
            fields.append(
                ("Expires", f"<t:{int(case.case_expires_at.timestamp())}:R>", True),
            )

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        # Set embed timestamp to case creation time
        if case.created_at:
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
