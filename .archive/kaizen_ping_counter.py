import datetime
import os

import discord
from discord.ext import commands
from loguru import logger


class KaizenPingCounter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ping_counter = 0
        log_path = "logs/kaizen_ping_counter.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        logger.add(log_path, rotation="00:00")
        self.last_reset_time = datetime.datetime.now()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        kaizen = self.bot.get_user(1046905234200469504)
        now = datetime.datetime.now()
        if now - self.last_reset_time > datetime.timedelta(hours=24):
            self.last_reset_time = now
            logger.info(f"Kaizen received {self.ping_counter} pings during the last 24 hours.")
            self.ping_counter = 0

        if kaizen in message.mentions:
            self.ping_counter += 1
            await message.reply(f"Kaizen has been pinged {self.ping_counter} times.")

        logger.info(f"Kaizen has been pinged {self.ping_counter} times.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(KaizenPingCounter(bot))
