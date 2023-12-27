from discord.ext import commands


class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith('!hello'):
            await message.channel.send('Hello!')


async def setup(bot):
    await bot.add_cog(OnMessage(bot))
