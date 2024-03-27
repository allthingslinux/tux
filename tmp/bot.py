import discord
from discord.ext import commands
from loguru import logger


class BotEventsCog(commands.Cog, name="Bot Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logger.info(f"{self.bot.user} has connected to Discord!")

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="All Things Linux",
            )
        )

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        logger.warning("Bot has disconnected from Discord.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BotEventsCog(bot))
