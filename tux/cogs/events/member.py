import discord
from discord.ext import commands
from loguru import logger


class MemberEventsCog(commands.Cog, name="Member Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        logger.info(f"User {user} was banned from {guild}.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        logger.info(f"Member joined: {member}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        logger.info(f"Member left: {member}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        logger.info(f"User {user} was unbanned from {guild}.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        logger.info(f"Member updated: {before} -> {after}")

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        logger.info(f"User updated: {before} -> {after}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberEventsCog(bot))
