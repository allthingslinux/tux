import discord
from discord.ext import commands
from loguru import logger


class ThreadEventsCog(commands.Cog, name="Thread Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        logger.trace(f"{thread} has been created.")

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread) -> None:
        logger.trace(f"{thread} has been deleted.")

    @commands.Cog.listener()
    async def on_thread_remove(self, thread: discord.Thread) -> None:
        logger.trace(f"{thread} has been removed.")

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread) -> None:
        logger.trace(f"Thread updated: {before} -> {after}")

    @commands.Cog.listener()
    async def on_thread_join(self, thread: discord.Thread) -> None:
        logger.trace(f"{thread} has been joined.")

    @commands.Cog.listener()
    async def on_thread_member_join(self, member: discord.ThreadMember) -> None:
        logger.trace(f"Member {member} joined the thread.")

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: discord.ThreadMember) -> None:
        logger.trace(f"Member {member} left the thread.")

    @commands.Cog.listener()
    async def on_thread_member_update(
        self, before: discord.ThreadMember, after: discord.ThreadMember
    ) -> None:
        logger.trace(f"Thread member updated: {before} -> {after}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ThreadEventsCog(bot))
