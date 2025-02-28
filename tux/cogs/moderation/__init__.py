import asyncio
from collections.abc import Sequence
from datetime import datetime
from typing import Any, TypeVar

import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils.constants import CONST
from tux.utils.exceptions import handle_case_result, handle_gather_result

T = TypeVar("T")


class ModerationCogBase(commands.Cog):
    DEFAULT_REASON = "No reason provided"

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.config = DatabaseController().guild_config

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
        final_reason: str,
        silent: bool,
        dm_action: str,
        actions: Sequence[tuple[Any, type[T]]] = (),
        duration: str | None = None,
    ) -> None:
        """
        Execute a moderation action with case creation, DM sending, and additional actions.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        case_type : CaseType
            The type of case to create.
        user : discord.Member | discord.User
            The target user of the moderation action.
        final_reason : str
            The reason for the moderation action.
        silent : bool
            Whether to send a DM to the user.
        dm_action : str
            The action description for the DM.
        actions : Sequence[tuple[Any, type[T]]]
            Additional actions to execute and their expected return types.
        duration : str | None
            The duration of the action, if applicable.
        """

        assert ctx.guild

        dm_task = self.send_dm(ctx, silent, user, final_reason, dm_action)

        case_task = self.db.case.insert_case(
            case_user_id=user.id,
            case_moderator_id=ctx.author.id,
            case_type=case_type,
            case_reason=final_reason,
            guild_id=ctx.guild.id,
        )
        action_tasks = [action[0] for action in actions]

        try:
            dm_result = await asyncio.wait_for(dm_task, timeout=2.0)
            dm_sent = self._handle_dm_result(user, dm_result)
        except TimeoutError:
            logger.warning(f"DM to {user} timed out")
            dm_sent = False
        except Exception as e:
            logger.warning(f"Failed to send DM to {user}: {e}")
            dm_sent = False

        # Then execute case creation and actions concurrently
        all_results = await asyncio.gather(case_task, *action_tasks, return_exceptions=True)
        case_result, *action_results = all_results

        # Handle case result
        case_result = handle_case_result(case_result)

        # Handle action results
        for result, (_, expected_type) in zip(action_results, actions, strict=False):
            handle_gather_result(result, expected_type)

        # Handle case response
        await self.handle_case_response(
            ctx,
            case_type,
            case_result.case_number,
            final_reason,
            user,
            dm_sent,
            duration,
        )

    def _handle_dm_result(self, user: discord.Member | discord.User, dm_result: Any) -> bool:
        """
        Handle the result of sending a DM.

        Parameters
        ----------
        user : discord.Member | discord.User
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
        timestamp : datetime | None, optional
            The timestamp for the embed, by default None (ctx.message.created_at).

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

        log_channel_id = await self.config.get_log_channel(ctx.guild.id, log_type)
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
        user : discord.Member | discord.User
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
                logger.warning(f"Failed to send DM to {user}. {e}")
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
        user : discord.Member
            The target of the moderation action.
        moderator : discord.Member | discord.User
            The moderator of the moderation action.
        action : str
            The action being performed.

        Returns
        -------
        bool
            Whether the conditions are met.
        """

        assert ctx.guild

        error_conditions = [
            (user == ctx.author, f"You cannot {action} yourself."),
            (
                isinstance(moderator, discord.Member)
                and isinstance(user, discord.Member)
                and user.top_role >= moderator.top_role,
                f"You cannot {action} a user with a higher or equal role.",
            ),
            (user == ctx.guild.owner, f"You cannot {action} the server owner."),
        ]

        for condition, error_message in error_conditions:
            if condition:
                embed = EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedCreator.ERROR,
                    user_name=ctx.author.name,
                    user_display_avatar=ctx.author.display_avatar.url,
                    description=error_message,
                )
                await ctx.send(embed=embed, ephemeral=True)
                return False

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
        case_number : int | None
            The case number.
        reason : str
            The reason for the case.
        user : discord.Member | discord.User
            The target of the case.
        dm_sent : bool
            Whether the DM was sent.
        duration : str | None, optional
            The duration of the case, by default None.
        """

        moderator = ctx.author

        fields = [
            ("Moderator", f"**{moderator}**\n`{moderator.id}`", True),
            ("Target", f"**{user}**\n`{user.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if case_number is not None:
            embed = self.create_embed(
                ctx,
                title=f"Case #{case_number} ({duration} {case_type})"
                if duration
                else f"Case #{case_number} ({case_type})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

            embed.set_thumbnail(url=user.avatar)

        else:
            embed = self.create_embed(
                ctx,
                title=f"Case #0 ({duration} {case_type})" if duration else f"Case #0 ({case_type})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

        embed.description = "-# DM successful" if dm_sent else "-# DM unsuccessful"

        await asyncio.gather(self.send_embed(ctx, embed, log_type="mod"), ctx.send(embed=embed, ephemeral=True))

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
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
            case_types=[CaseType.POLLBAN, CaseType.POLLUNBAN],
        )

        # If no cases exist or latest case is an unban, user is not banned
        return bool(latest_case and latest_case.case_type != CaseType.POLLUNBAN)

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
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
            case_types=[CaseType.SNIPPETBAN, CaseType.SNIPPETUNBAN],
        )

        # If no cases exist or latest case is an unban, user is not banned
        return bool(latest_case and latest_case.case_type != CaseType.SNIPPETUNBAN)
