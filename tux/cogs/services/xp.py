from pathlib import Path

import discord
import yaml
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.main import get_prefix

settings_path = Path("config/settings.yml")
with settings_path.open() as file:
    settings = yaml.safe_load(file)


class Levelling(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()

    @commands.Cog.listener("on_message")
    async def xp_listener(self, message: discord.Message) -> None:
        """
        Listens for messages and processes XP gain and level up.

        Args:
            message (discord.Message): The message object.
        """
        if message.author.bot or message.guild is None:
            return

        if message.channel.id in settings["XP_BLACKLIST_CHANNEL"]:
            return

        prefixes = await get_prefix(self.bot, message)
        if any(message.content.startswith(prefix) for prefix in prefixes):
            return

        member = message.guild.get_member(message.author.id)
        if member is None:
            return

        guild = message.guild

        await self.levels_controller.increment_xp(member.id, guild.id, member, guild)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Levelling(bot))
