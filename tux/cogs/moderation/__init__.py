from datetime import datetime

import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


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

        embed = discord.Embed(color=color, timestamp=timestamp or ctx.message.created_at)
        embed.set_author(name=title, icon_url=icon_url)
        embed.set_thumbnail(url=thumbnail_url)

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=self.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)

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
    ) -> None:
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
                await user.send(
                    f"You have been {action} from {ctx.guild} for the following reason:\n> {reason}",
                )

            except (discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Failed to send DM to {user}. {e}")
                await ctx.send(f"Failed to send DM to {user}. {e}", delete_after=30, ephemeral=True)

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
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
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
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
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
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
            return False

        return True

    async def check_jail_conditions(
        self,
        ctx: commands.Context[Tux],
        user: discord.Member,
    ) -> tuple[bool, discord.Role | None, discord.abc.GuildChannel | None]:
        """
        Validate jail role and channel existence and member condition.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        user : discord.Member
            The member to jail.

        Returns
        -------
        tuple
            A tuple containing a boolean indicating success, the jail role, and the jail channel.
        """
        assert ctx.guild

        jail_role_id = await self.config.get_jail_role_id(ctx.guild.id)
        jail_role = ctx.guild.get_role(jail_role_id) if jail_role_id else None
        jail_channel_id = await self.config.get_jail_channel_id(ctx.guild.id)
        jail_channel = ctx.guild.get_channel(jail_channel_id) if jail_channel_id else None

        if jail_role is None:
            await ctx.send("The jail role has been deleted or not set up.", delete_after=30, ephemeral=True)
            return False, None, None
        if jail_channel is None:
            await ctx.send("The jail channel has been deleted or not set up.", delete_after=30, ephemeral=True)
            return False, None, None
        if jail_role in user.roles:
            await ctx.send("The user is already jailed.", delete_after=30, ephemeral=True)
            return False, None, None

        return True, jail_role, jail_channel

    async def handle_case_response(
        self,
        ctx: commands.Context[Tux],
        case_type: CaseType,
        case_number: int | None,
        reason: str,
        user: discord.Member | discord.User,
        duration: str | None = None,
    ):
        moderator = ctx.author

        fields = [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{user}__\n`{user.id}`", True),
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

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.send(embed=embed, delete_after=30, ephemeral=True)
