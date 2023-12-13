from discord.ext import commands


class OnJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Your on_join logic goes here
        print(f'{member} has joined the server.')


async def setup(bot):
    await bot.add_cog(OnJoin(bot))
