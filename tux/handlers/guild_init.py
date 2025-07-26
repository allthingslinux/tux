"""Ensure guild + guild_config rows exist when the bot starts or joins a guild."""
from __future__ import annotations

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers.guild import GuildController
from tux.database.controllers.guild_config import GuildConfigController


class GuildInit(commands.Cog):
    def __init__(self, bot: Tux):
        self.bot = bot
        self.guild_controller = GuildController()
        self.guild_config_controller = GuildConfigController()

    async def cog_load(self) -> None:  # called by discord.py 2.4+
        # Ensure DB rows for all guilds we are already in
        for guild in self.bot.guilds:
            await self._ensure_guild(guild.id)

    async def _ensure_guild(self, guild_id: int) -> None:
        # Upsert guild and guild_config rows
        await self.guild_controller.get_or_create_guild(guild_id)
        if await self.guild_config_controller.get_guild_config(guild_id) is None:
            await self.guild_config_controller.insert_guild_config(guild_id)

    # When the bot is added to a new guild
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self._ensure_guild(guild.id)


async def setup(bot: Tux) -> None:
    await bot.add_cog(GuildInit(bot))