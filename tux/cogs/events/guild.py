from datetime import datetime

import discord
from discord.ext import commands
from loguru import logger


class GuildEventsCog(commands.Cog, name="Guild Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        logger.info(f"{channel} has been created in {channel.guild}.")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        logger.info(f"{channel} has been deleted in {channel.guild}.")

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(
        self,
        channel: discord.abc.GuildChannel | discord.Thread,
        last_pin: datetime | None,
    ) -> None:
        logger.info(f"Pins in  #{channel.name} have been updated. Last pin: {last_pin}")

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ) -> None:
        logger.info(f"Channel updated: {before} -> {after}")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        logger.info(f"Role created: {role}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        logger.info(f"Role deleted: {role}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        logger.info(f"Role updated: {before} -> {after}")

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        logger.info(f"Guild updated: {before} -> {after}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildEventsCog(bot))
