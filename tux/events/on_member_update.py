import discord
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMemberUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_member_update")
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Handles the event when a Discord member updates their profile.

        This function is triggered when a member's nickname, roles, pending status, timeout status, guild avatar, or flags are modified. It does not react when a member's timeout expires due to a restriction in Discord.

        Args:
            before (discord.Member): The previous state of the member before the update.
            after (discord.Member): The updated state of the member after the update.

        Note:
            This function requires the `Intents.members` to be enabled.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_update
        """  # noqa E501

        # TODO: On member update logic goes here.

        # You can use the before and after objects to compare the changes.
        # We should probably abstract this into multiple functions:

        # 1. Comparing changes
        # 2. Logging changes
        # 3. Creating the embed
        # 4. Sending the embed

        logger.debug(f"Member {before} updated to {after}.")


async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))
