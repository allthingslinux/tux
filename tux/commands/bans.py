import logging
from discord.ext import commands
from utils._tux_logger import TuxLogger
import discord
from discord import app_commands

logger = TuxLogger(__name__)


class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command(name='tban')
    # async def temp_ban(self,
    #                    ctx,
    #                    user: commands.MemberConverter,
    #                    duration: int,
    #                    reason: str):
    #     """
    #     Temporarily ban a user.
    #     Example: !tban @user 7 Violating rules
    #     """
    #     await ctx.guild.ban(user, reason=reason)
    #     logger.info(f"Temporarily banned {user} for {duration} days. Reason: {reason}")
    #
    # @commands.command(name='qban')
    # async def quick_ban(self,
    #                     ctx,
    #                     user: commands.MemberConverter):
    #     """
    #     Quickly ban a user.
    #     Example: !qban @user
    #     """
    #     await ctx.guild.ban(user)
    #     logger.info(f"Quickly banned {user}")

    @commands.cog_slash(name="ban", description="jfdahfakj")
    async def ban(self,
                  interaction: discord.Interaction,
                  user: commands.MemberConverter,
                  reason: str = 'Offensive Language',
                  time: app_commands.Range[int, 0, 999] = -1):
        """
        Permanently ban a user.
        Example: !ban @user Violating rules
        """
        await interaction.guild.ban(
            user,
            reason=reason,
            delete_message_days=0
        )
        logger.info(f"{interaction.author} Permanently banned {user}. Reason: {reason}")

    @commands.command()
    @app_commands.describe(fruit='The fruit to choose')
    async def fruit(interaction: discord.Interaction, fruit):
        """Choose a fruit!"""
        await interaction.response.send_message(fruit)

    # @ban.autocomplete('user')
    # async def ban_autocompletion(
    #         user: commands.MemberConverter,
    #         current: str
    #         ) -> typing.List[app_commands.Choice[str]]:
    #     data = []
    #     for hi in ['hi', 'hi2', 'hi3']:
    #         data.append(app_commands.Choice(name=hi, value=hi))
    #     return data


async def setup(bot, debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)
    await bot.add_cog(BanCog(bot))
