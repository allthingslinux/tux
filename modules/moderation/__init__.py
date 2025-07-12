import asyncio
from asyncio import Lock
from collections.abc import Callable, Coroutine, Sequence
from datetime import datetime
from typing import Any, ClassVar, TypeVar

import discord
from bot import Tux
from database.controllers import DatabaseController
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator, EmbedType
from utils.constants import CONST
from utils.exceptions import handle_case_result, handle_gather_result

from prisma.enums import CaseType

T = TypeVar("T")
R = TypeVar("R")  # Return type for generic functions


class ModerationCogBase(commands.Cog):
    # Actions that remove users from the server, requiring DM to be sent first
    REMOVAL_ACTIONS: ClassVar[set[CaseType]] = {CaseType.BAN, CaseType.KICK, CaseType.TEMPBAN}

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()

        # Dictionary to store locks per user
        self._user_action_locks: dict[int, Lock] = {}
        # Threshold to trigger cleanup of unused user locks
        self._lock_cleanup_threshold: int = 100  # Sourcery suggestion

    async def get_user_lock(self, user_id: int) -> Lock:
        """
        Get or create a lock for operations on a specific user.
        If the number of stored locks exceeds the cleanup threshold, unused locks are removed.

        Parameters
        ----------
        user_id : int
            The ID of the user to get a lock for.

        Returns
        -------
        Lock
            The lock for the user.
        """
        # Cleanup check
        if len(self._user_action_locks) > self._lock_cleanup_threshold:
            await self.clean_user_locks()

        if user_id not in self._user_action_locks:
            self._user_action_locks[user_id] = Lock()
        return self._user_action_locks[user_id]

    # New method for cleaning locks
    async def clean_user_locks(self) -> None:
        """
        Remove locks for users that are not currently in use.
        Iterates through the locks and removes any that are not currently locked.
        """
        # Create a list of user_ids to avoid RuntimeError for changing dict size during iteration.
        unlocked_users: list[int] = []
        unlocked_users.extend(user_id for user_id, lock in self._user_action_locks.items() if not lock.locked())
        removed_count = 0
        for user_id in unlocked_users:
            if user_id in self._user_action_locks:
                del self._user_action_locks[user_id]
                removed_count += 1

        if removed_count > 0:
            remaining_locks = len(self._user_action_locks)
            logger.debug(f"Cleaned up {removed_count} unused user action locks. {remaining_locks} locks remaining.")

    async def execute_user_action_with_lock(
        self,
        user_id: int,
        action_func: Callable[..., Coroutine[Any, Any, R]],
        *args: Any,
        **kwargs: Any,
    ) -> R:
        """
        Execute an action on a user with a lock to prevent race conditions.

        Parameters
        ----------
        user_id : int
            The ID of the user to lock.
        action_func : Callable[..., Coroutine[Any, Any, R]]
            The coroutine function to execute.
        *args : Any
            Arguments to pass to the function.
        **kwargs : Any
            Keyword arguments to pass to the function.

        Returns
        -------
        R
            The result of the action function.
        """
        lock = await self.get_user_lock(user_id)

        async with lock:
            return await action_func(*args, **kwargs)

    async def _dummy_action(self) -> None:
        """
        Dummy coroutine for moderation actions that only create a case without performing Discord API actions.
        Used by commands like warn, pollban, snippetban etc. that only need case creation.
        """
        return

    async def execute_mod_action(
        self,
        ctx: commands.Context[Tux],
        case_type: CaseType,
        user: discord.Member | discord.User,
        reason: str,
        silent: bool,
        dm_action: str,
        actions: Sequence[tuple[Any, type[R]]] = (),
        duration: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
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

        # For actions that remove users from the server, send DM first
        if case_type in self.REMOVAL_ACTIONS and not silent:
            try:
                # Attempt to send DM before banning/kicking
                dm_sent = await asyncio.wait_for(self.send_dm(ctx, silent, user, reason, dm_action), timeout=2.0)
            except TimeoutError:
                logger.warning(f"DM to {user} timed out before {case_type}")
                dm_sent = False
            except Exception as e:
                logger.warning(f"Failed to send DM to {user} before {case_type}: {e}")
                dm_sent = False
        else:
            # For other actions, we'll handle DM after the action
            dm_sent = False

        # Execute Discord API actions
        action_results: list[Any] = []
        for action, expected_type in actions:
            try:
                result = await action
                action_results.append(handle_gather_result(result, expected_type))
            except Exception as e:
                logger.error(f"Failed to execute action on {user}: {e}")
                # Raise to stop the entire operation if the primary action fails
                raise

        # For actions that don't remove users, send DM after action is taken
        if case_type not in self.REMOVAL_ACTIONS and not silent:
            try:
                dm_task = self.send_dm(ctx, silent, user, reason, dm_action)
                dm_result = await asyncio.wait_for(dm_task, timeout=2.0)
                dm_sent = self._handle_dm_result(user, dm_result)
            except TimeoutError:
                logger.warning(f"DM to {user} timed out")
                dm_sent = False
            except Exception as e:
                logger.warning(f"Failed to send DM to {user}: {e}")
                dm_sent = False

        # Create the case in the database
        try:
            case_result = await self.db.case.insert_case(
                guild_id=ctx.guild.id,
                case_user_id=user.id,
                case_moderator_id=ctx.author.id,
                case_type=case_type,
                case_reason=reason,
                case_expires_at=expires_at,
            )

            case_result = handle_case_result(case_result) if case_result is not None else None

        except Exception as e:
            logger.error(f"Failed to create case for {user}: {e}")
            # Continue execution to at least notify the moderator
            case_result = None

        # Handle case response
        await self.handle_case_response(
            ctx,
            case_type,
            case_result.case_number if case_result else None,
            reason,
            user,
            dm_sent,
            duration,
        )

    def _handle_dm_result(self, user: discord.Member | discord.User, dm_result: Any) -> bool:
        """
        Handle the result of sending a DM.

        Parameters
        ----------
        user : Union[discord.Member, discord.User]
            The user the DM was sent to.
        dm_result : Any
            The result of the DM sending operation.

        Returns
        -------
        bool
            Whether the DM was successfully sent.
        """

        if isinstance(dm_result, Exception):
            logger.warning(f"Failed to send DM to {user}: {dm_result}")
            return False

        return dm_result if isinstance(dm_result, bool) else False

    async def send_error_response(
        self,
        ctx: commands.Context[Tux],
        error_message: str,
        error_detail: Exception | None = None,
        ephemeral: bool = True,
    ) -> None:
        """
        Send a standardized error response.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        error_message : str
            The error message to display.
        error_detail : Optional[Exception]
            The exception details, if available.
        ephemeral : bool
            Whether the message should be ephemeral.
        """
        if error_detail:
            logger.error(f"{error_message}: {error_detail}")

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            description=error_message,
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    def create_embed(
        self,
        ctx: commands.Context[Tux],
        title: str,
        fields: list[tuple[str, str, bool]],
        color: int,
        icon_url: str,
        timestamp: datetime | None = None,
        thumbnail_url: str | None = None,
    ) -> discord.Embed:
        """
        Create an embed for moderation actions.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        title : str
            The title of the embed.
        fields : list[tuple[str, str, bool]]
            The fields to add to the embed.
        color : int
            The color of the embed.
        icon_url : str
            The icon URL for the embed.
        timestamp : Optional[datetime]
            The timestamp for the embed.
        thumbnail_url : Optional[str]
            The thumbnail URL for the embed.

        Returns
        -------
        discord.Embed
            The embed for the moderation action.
        """

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=self.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            custom_color=color,
            message_timestamp=timestamp or ctx.message.created_at,
            custom_author_text=title,
            custom_author_icon_url=icon_url,
            thumbnail_url=thumbnail_url,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        return embed

    async def send_embed(
        self,
        ctx: commands.Context[Tux],
        embed: discord.Embed,
        log_type: str,
    ) -> None:
        """
        Send an embed to the log channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        embed : discord.Embed
            The embed to send.
        log_type : str
            The type of log to send the embed to.
        """

        assert ctx.guild

        log_channel_id = await self.db.guild_config.get_log_channel(ctx.guild.id, log_type)

        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)

            if isinstance(log_channel, discord.TextChannel):
                await log_channel.send(embed=embed)

    async def send_dm(
        self,
        ctx: commands.Context[Tux],
        silent: bool,
        user: discord.Member | discord.User,
        reason: str,
        action: str,
    ) -> bool:
        """
        Send a DM to the target user.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        silent : bool
            Whether the command is silent.
        user : Union[discord.Member, discord.User]
            The target of the moderation action.
        reason : str
            The reason for the moderation action.
        action : str
            The action being performed.

        Returns
        -------
        bool
            Whether the DM was successfully sent.
        """

        if not silent:
            try:
                await user.send(f"You have been {action} from {ctx.guild} for the following reason:\n> {reason}")
            except (discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Failed to send DM to {user}: {e}")
                return False
            else:
                return True
        else:
            return False

    async def check_conditions(
        self,
        ctx: commands.Context[Tux],
        user: discord.Member | discord.User,
        moderator: discord.Member | discord.User,
        action: str,
    ) -> bool:
        """
        Check if the conditions for the moderation action are met.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        user : Union[discord.Member, discord.User]
            The target of the moderation action.
        moderator : Union[discord.Member, discord.User]
            The moderator of the moderation action.
        action : str
            The action being performed.

        Returns
        -------
        bool
            Whether the conditions are met.
        """

        assert ctx.guild

        # Check common failure conditions first
        fail_reason = None

        # Self-moderation check
        if user.id == moderator.id:
            fail_reason = f"You cannot {action} yourself."
        # Guild owner check
        elif user.id == ctx.guild.owner_id:
            fail_reason = f"You cannot {action} the server owner."
        # Role hierarchy check - only applies when both are Members
        elif (
            isinstance(user, discord.Member)
            and isinstance(moderator, discord.Member)
            and user.top_role >= moderator.top_role
        ):
            fail_reason = f"You cannot {action} a user with a higher or equal role."

        # If we have a failure reason, send the embed and return False
        if fail_reason:
            await self.send_error_response(ctx, fail_reason)
            return False

        # All checks passed
        return True

    async def handle_case_response(
        self,
        ctx: commands.Context[Tux],
        case_type: CaseType,
        case_number: int | None,
        reason: str,
        user: discord.Member | discord.User,
        dm_sent: bool,
        duration: str | None = None,
    ) -> None:
        """
        Handle the response for a case.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        case_type : CaseType
            The type of case.
        case_number : Optional[int]
            The case number.
        reason : str
            The reason for the case.
        user : Union[discord.Member, discord.User]
            The target of the case.
        dm_sent : bool
            Whether the DM was sent.
        duration : Optional[str]
            The duration of the case.
        """

        moderator = ctx.author

        fields = [
            ("Moderator", f"-# **{moderator}**\n-# `{moderator.id}`", True),
            ("Target", f"-# **{user}**\n-# `{user.id}`", True),
            ("Reason", f"-# > {reason}", False),
        ]

        title = self._format_case_title(case_type, case_number, duration)

        embed = self.create_embed(
            ctx,
            title=title,
            fields=fields,
            color=CONST.EMBED_COLORS["CASE"],
            icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
        )

        embed.description = "-# DM sent" if dm_sent else "-# DM not sent"

        await asyncio.gather(self.send_embed(ctx, embed, log_type="mod"), ctx.send(embed=embed, ephemeral=True))

    def _format_case_title(self, case_type: CaseType, case_number: int | None, duration: str | None) -> str:
        """
        Format a case title.

        Parameters
        ----------
        case_type : CaseType
            The type of case.
        case_number : Optional[int]
            The case number.
        duration : Optional[str]
            The duration of the case.

        Returns
        -------
        str
            The formatted case title.
        """
        case_num = case_number if case_number is not None else 0
        if duration:
            return f"Case #{case_num} ({duration} {case_type})"
        return f"Case #{case_num} ({case_type})"

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
        # Get latest case for this user
        return await self.db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.POLLBAN,
            inactive_restriction_type=CaseType.POLLUNBAN,
        )

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
        # Get latest case for this user
        return await self.db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.SNIPPETBAN,
            inactive_restriction_type=CaseType.SNIPPETUNBAN,
        )

    async def is_jailed(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is jailed using the optimized latest case method.

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
        # Get latest case for this user
        return await self.db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.JAIL,
            inactive_restriction_type=CaseType.UNJAIL,
        )
