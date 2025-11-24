"""Support forum thread notification system.

This plugin monitors support forum threads and notifies designated roles
when new support threads are created. It provides formatted notifications
with thread information, tags, and user mentions.
"""

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.ui.embeds import EmbedCreator, EmbedType

# Configuration

SUPPORT_FORUM_ID = 1172312653797007461  # support forum to monitor
SUPPORT_ROLE_ID = (
    1274823545087590533  # who to ping when a new support thread is created
)
PING_CHANNEL_ID = 1172245377395728467  # where to send the notification

# -- DO NOT CHANGE ANYTHING BELOW THIS LINE --


class SupportNotifier(BaseCog):
    """Discord cog for monitoring and notifying about support forum threads.

    This cog listens for new thread creation events in the configured support
    forum and sends notifications to designated roles with thread information.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the SupportNotifier cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """
        Handle new thread creation events.

        Monitors for new threads in the support forum and sends notifications
        to designated roles with thread information and tags.

        Parameters
        ----------
        thread : discord.Thread
            The newly created thread.
        """
        if thread.parent_id == SUPPORT_FORUM_ID:
            owner_mention = thread.owner.mention if thread.owner else {thread.owner_id}

            if tags := [tag.name for tag in thread.applied_tags]:
                tag_list = ", ".join(tags)
                msg = f"<:tux_notify:1274504953666474025> **New support thread created** - help is appreciated!\n{thread.mention} by {owner_mention}\n<:tux_tag:1274504955163709525> **Tags**: `{tag_list}`"

            else:
                msg = f"<:tux_notify:1274504953666474025> **New support thread created** - help is appreciated!\n{thread.mention} by {owner_mention}"

            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                description=msg,
                custom_color=discord.Color.random(),
                hide_author=True,
            )

            channel = self.bot.get_channel(PING_CHANNEL_ID)

            if channel is not None and isinstance(channel, discord.TextChannel):
                await channel.send(content=f"<@&{SUPPORT_ROLE_ID}>", embed=embed)


async def setup(bot: Tux) -> None:
    """
    Set up the SupportNotifier cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(SupportNotifier(bot))
