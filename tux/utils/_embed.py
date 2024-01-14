# utils/_embed.py

import discord

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Embed:
    """This class is a wrapper around discord.Embed. It provides additional functionality
    such as adding fields and sending the embed to a channel. It also provides a
    default embed template for the bot.
    """

    def __init__(self, bot, color=0x7289DA):
        self.bot = bot
        self.default_color = color
        self.default_channels = {
            "audit": 1191472088695980083,
            # add more embed type: channel_id mappings here
        }

    def process_embed(self, embed_attr):
        embed = discord.Embed()

        for attr, value in embed_attr.items():
            if attr == "fields" and isinstance(value, list):
                for field in value:
                    embed.add_field(**field)
            else:
                setattr(embed, attr, value)

        return embed

    async def send_embed(self, channel_id, **embed_attr):
        """Send an embed to a channel."""
        channel = self.bot.get_channel(channel_id)

        embed_attr["color"] = embed_attr.get("color", self.default_color)

        embed = self.process_embed(embed_attr)
        await channel.send(embed=embed)

    async def send_audit_embed(self, channel_id=None, **embed_attr):
        """Send an audit embed to a channel."""
        if channel_id is None:
            channel_id = self.default_channels["audit"]

        embed_attr["color"] = 0x00FF00
        await self.send_embed(channel_id, **embed_attr)
