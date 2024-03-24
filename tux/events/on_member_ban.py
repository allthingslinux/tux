# on_member_ban.py
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMemberBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """
        Handles the event when a user gets banned from a Discord Guild.

        This function is called when a user gets banned from a Guild.

        Note:
            This function requires the `Intents.moderation` to be enabled.

        Args:
            guild (discord.Guild): The guild the user got banned from.
            user (Union[User, Member]): The user that got banned. Can be either User
            or Member depending on if the user was in the guild or not at the time of removal.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_ban
        """  # noqa E501

        logger.info(f"{user} has been banned from the server.")


async def setup(bot):
    await bot.add_cog(OnMemberBan(bot))
