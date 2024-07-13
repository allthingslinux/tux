from datetime import datetime

import discord
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.embeds import create_embed_footer

# TODO: Move command permission checks to the base class


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
        if not silent:
            try:
                await target.send(
                    f"You have been {action} from {ctx.guild} for the following reason:\n> {reason}",
                )
            except (discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Failed to send DM to {target}. {e}")
                await ctx.send(f"Failed to send DM to {target}. {e}", delete_after=10, ephemeral=True)
