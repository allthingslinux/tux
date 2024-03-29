# Import the necessary modules
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

# Initialize the logger
logger = TuxLogger(__name__)


# TODO:
# Properly account for all important changes
# Ensure that some changes are not using fields (e.g. roles, permissions, etc.)...
# this is because fields are limited in character count


class OnMemberUpdate(commands.Cog):
    # Initialize the class with the bot as an argument
    def __init__(self, bot):
        self.bot = bot

    # Define a listener for the 'on_member_update' event
    @commands.Cog.listener("on_member_update")
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        This function is triggered when a member's profile is updated. It
        compares the before and after states of the member, logs any changes,
        creates an embed for the changes, and sends the embed to a specified
        channel.
        """  # noqa E501

        try:
            # Compare the before and after states of the member
            changes = self.compare_member_changes(before, after)
            if changes:
                # Log the changes
                self.log_member_changes(changes)
                # Create an embed for the changes
                embed = self.create_embed_for_changes(changes)
                # Send the embed to a specified channel
                await self.send_embed(embed)
        except Exception as e:
            # Log any errors that occur
            logger.error(f"Error handling member update: {e}")

    def compare_member_changes(self, before, after):
        """
        This function compares the before and after states of a member.
        It currently only checks for changes in nickname, but more comparisons can be added as needed.
        """
        changes = {}
        logger.info(f"Comparing {before} to {after}.")
        if before.nick != after.nick:
            changes["nickname"] = {"before": before.nick, "after": after.nick}

        return changes

    def log_member_changes(self, changes):
        """
        This function logs any changes that have occurred.
        """
        for change, values in changes.items():
            logger.info(f"{change} changed from {values['before']} to {values['after']}")

    def create_embed_for_changes(self, changes):
        """
        This function creates an embed for the changes that have occurred.
        """
        embed = discord.Embed(
            title="Member Update", description="A member has updated their profile."
        )
        for change, values in changes.items():
            embed.add_field(name=f"Old {change}", value=values["before"], inline=False)
            embed.add_field(name=f"New {change}", value=values["after"], inline=False)

        logger.info("Embed created.")
        return embed

    async def send_embed(self, embed):
        channel_id = 1191472088695980083
        channel = self.bot.get_channel(channel_id)
        await channel.send(embed=embed)
        logger.info(f"Embed sent to channel {channel_id}.")


# Define an asynchronous setup function that adds the OnMemberUpdate cog to the bot
async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))
