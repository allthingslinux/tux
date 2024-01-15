import discord

from tux.constants import C
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Embed:
    """
    This class is a wrapper around discord.Embed. It provides additional functionality,
    including adding fields and the ability to send the embed to a channel. It also offers
    a default embed template for the bot.
    """

    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, attributes):
        embed = discord.Embed()

        for attr, value in attributes.items():
            if attr == "fields" and isinstance(value, list | tuple):
                for field in value:
                    embed.add_field(**field)
            else:
                setattr(embed, attr, value)
        return embed

    async def send_embed(self, channel_id, **attributes):
        """Sends an embed message to a discord channel"""
        channel = self.bot.get_channel(channel_id)
        attributes["color"] = attributes.get("color", C.COLORS["default"])

        embed = self.create_embed(attributes)
        return await channel.send(embed=embed)

    async def send_audit_embed(self, channel_id: int | None = None, **embed_attr):
        """Send an audit embed to a channel."""
        if channel_id is None:
            channel_id = C.CHANNELS["audit"]

        embed_attr["color"] = C.COLORS["info"]
        await self.send_embed(channel_id, **embed_attr)
