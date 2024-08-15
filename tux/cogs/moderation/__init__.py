from datetime import datetime

import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.embeds import create_embed_footer


class ModerationCogBase(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.config = DatabaseController().guild_config

    async def create_embed(
        self,
        ctx: commands.Context[commands.Bot],
        title: str,
        fields: list[tuple[str, str, bool]],
        color: int,
        icon_url: str,
        timestamp: datetime | None = None,
    ) -> discord.Embed:
        """
        Create an embed for moderation actions.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
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

        footer_text, footer_icon_url = create_embed_footer(ctx)
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        return embed

    async def send_embed(
        self,
        ctx: commands.Context[commands.Bot],
        embed: discord.Embed,
        log_type: str,
    ) -> None:
        """
        Send an embed to the log channel.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context of the command.
        embed : discord.Embed
            The embed to send.
        log_type : str
            The type of log to send the embed to.
        """

        if ctx.guild:
            log_channel_id = await self.config.get_log_channel(ctx.guild.id, log_type)
            if log_channel_id:
                log_channel = ctx.guild.get_channel(log_channel_id)
                if isinstance(log_channel, discord.TextChannel):
                    await log_channel.send(embed=embed)

    async def send_dm(
        self,
        ctx: commands.Context[commands.Bot],
        silent: bool,
        target: discord.Member,
        reason: str,
        action: str,
    ) -> None:
        """
        Send a DM to the target user.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context of the command.
        silent : bool
            Whether the command is silent.
        target : discord.Member
            The target of the moderation action.
        reason : str
            The reason for the moderation action.
        action : str
            The action being performed.
        """

        if not silent:
            try:
                await target.send(
                    f"You have been {action} from {ctx.guild} for the following reason:\n> {reason}",
                )

            except (discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Failed to send DM to {target}. {e}")
                await ctx.send(f"Failed to send DM to {target}. {e}", delete_after=30, ephemeral=True)

    async def check_conditions(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        moderator: discord.Member | discord.User,
        action: str,
    ) -> bool:
        """
        Check if the conditions for the moderation action are met.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context of the command.
        target : discord.Member
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

        if ctx.guild is None:
            logger.warning(f"{action.capitalize()} command used outside of a guild context.")
            return False

        if target == ctx.author:
            await ctx.send(f"You cannot {action} yourself.", delete_after=30, ephemeral=True)
            return False

        if isinstance(moderator, discord.Member) and target.top_role >= moderator.top_role:
            await ctx.send(f"You cannot {action} a user with a higher or equal role.", delete_after=30, ephemeral=True)
            return False

        if target == ctx.guild.owner:
            await ctx.send(f"You cannot {action} the server owner.", delete_after=30, ephemeral=True)
            return False

        return True
