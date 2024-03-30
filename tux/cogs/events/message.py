import discord
from discord.ext import commands
from loguru import logger


class MessageEventsCog(commands.Cog, name="Message Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]) -> None:
        logger.trace(f"Messages deleted: {messages}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        logger.trace(f"Message deleted: {message}")

        # if sender is a bot, ignore, some bots delete their own messages
        if message.author.bot:
            return

        # check if message has a ping (role, user, etc.)
        if message.mentions or message.role_mentions:
            if len(message.mentions) == 1 and message.mentions[0] == message.author:
                return
            embed = discord.Embed(
                title="Ghost Ping!", color=discord.Color.red(), timestamp=message.created_at
            )
            embed.add_field(name="Sender", value=message.author.mention, inline=True)
            # if mentions add mentions field, if role_mentions add role_mentions field
            if message.mentions:
                embed.add_field(
                    name="Mentions",
                    value=", ".join([mention.mention for mention in message.mentions]),
                    inline=True,
                )
            if message.role_mentions:
                embed.add_field(
                    name="Role Mentions",
                    value=", ".join([role.mention for role in message.role_mentions]),
                    inline=True,
                )
            elif not message.mentions and not message.role_mentions:
                # this will (probably) never happen, but just in case
                embed.add_field(
                    name="whgar?", value="something is wrong here, no mentions found", inline=True
                )

            await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        logger.trace(f"Message edited: {before} -> {after}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        logger.trace(f"Message received: {message}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageEventsCog(bot))
