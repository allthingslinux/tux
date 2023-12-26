import logging
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='tban')
    async def temp_ban(self,
                       ctx,
                       user: commands.MemberConverter,
                       duration: int,
                       reason: str):
        """
        Temporarily ban a user.
        Example: !tban @user 7 Violating rules
        """
        await ctx.guild.ban(user, reason=reason)
        logger.info(f"Temporarily banned {user} for {duration} days. Reason: {reason}")

    @commands.command(name='qban')
    async def quick_ban(self,
                        ctx,
                        user: commands.MemberConverter):
        """
        Quickly ban a user.
        Example: !qban @user
        """
        await ctx.guild.ban(user)
        logger.info(f"Quickly banned {user}")

    @commands.command(name='ban')
    async def perm_ban(self,
                       ctx,
                       user: commands.MemberConverter,
                       reason: str):
        """
        Permanently ban a user.
        Example: !ban @user Violating rules
        """
        await ctx.guild.ban(
            user,
            reason=reason,
            delete_message_days=0
        )
        logger.info(f"Permanently banned {user}. Reason: {reason}")


async def setup(bot, debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)
    await bot.add_cog(BanCog(bot))
