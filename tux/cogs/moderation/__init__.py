import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils.constants import CONST


class ModerationCogBase(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.config = DatabaseController().guild_config

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
        user: discord.Member,
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
        user : discord.Member
            The target of the moderation action.
        reason : str
            The reason for the moderation action.
        action : str
            The action being performed.
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
        user: discord.Member,
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

        if user == ctx.author:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="You cannot self-moderate",
                description=f"You cannot {action} yourself.",
            )
            await ctx.send(embed=embed, ephemeral=True)
            return False

        if isinstance(moderator, discord.Member) and user.top_role >= moderator.top_role:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="You cannot self-moderate",
                description=f"You cannot {action} a user with a higher or equal role.",
            )
            await ctx.send(embed=embed, ephemeral=True)
            return False

        if user == ctx.guild.owner:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="You cannot self-moderate",
                description=f"You cannot {action} the server owner.",
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
    ):
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

        ban_cases = await self.db.case.get_all_cases_by_type(guild_id, CaseType.POLLBAN)
        unban_cases = await self.db.case.get_all_cases_by_type(guild_id, CaseType.POLLUNBAN)

        ban_count = sum(case.case_user_id == user_id for case in ban_cases)
        unban_count = sum(case.case_user_id == user_id for case in unban_cases)

        return ban_count > unban_count
