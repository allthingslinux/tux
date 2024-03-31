import discord
from discord.ext import commands
from loguru import logger


class GhostPings(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        logger.trace(f"Message deleted: {message}")

        # if sender is a bot, ignore, some bots delete their own messages
        if message.author.bot:
            return

        # check if message has a ping (role, user, etc.)
        if message.mentions or message.role_mentions:
            if len(message.mentions) == 1 and (message.mentions[0] == message.author) or (message.mentions[0].bot):
                return

            embed = discord.Embed(
                title="Ghost Ping!", color=discord.Color.red(), timestamp=message.created_at
            )

            embed.description = f"{message.author.mention} pinged: {', '.join([mention.mention for mention in message.mentions])} {', '.join([role.mention for role in message.role_mentions])}"

            await message.channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GhostPings(bot))
