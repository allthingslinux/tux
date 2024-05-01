import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class GuildLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audit_log_channel_id: int = CONST.LOG_CHANNELS["AUDIT"]

    async def send_to_audit_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(self.audit_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # check if the message has no embeds, attachments, or content, stickers, or isnt a nitro gift/boost
        # if so its probably a poll
        poll_channel = self.bot.get_channel(1228717294788673656)
        if message.channel == poll_channel:
            # check if the message has content, stickers, or attachments
            # if so delete the message as its not a poll
            if message.content or message.stickers or message.attachments:
                await message.delete()
                embed = EmbedCreator.create_log_embed(
                    title="Non-Poll Deleted",
                    description=f"Message: {message.id}",
                )
                await self.send_to_audit_log(embed)
                return

            # make a thread for the poll
            await message.create_thread(
                name=f"Poll by {message.author.display_name}",
                reason="Poll thread",
            )
            return

        if (
            not message.embeds
            and not message.attachments
            and not message.content
            and not message.stickers
        ):
            # check if the message is not a message
            if message.type != discord.MessageType.default:
                return
            # delete the message and log it
            await message.delete()
            embed = EmbedCreator.create_log_embed(
                title="Poll Deleted",
                description=f"Message: {message.id}",
            )
            await self.send_to_audit_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildLogging(bot))
