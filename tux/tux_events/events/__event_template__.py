from discord.ext import commands


class CogTemplate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello', help='Responds with a greeting.')
    async def hello(self, ctx):
        """
        An example hello world command.
        
        Parameters:
        - ctx (commands.Context): The context of the command.

        Example usage:
        !hello
        """
        await ctx.send('world!')

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        An event listener that triggers when a message is sent. You can find a
        list of these at
        https://discordpy.readthedocs.io/en/latest/api.html#event-reference

        Parameters:
        - message (discord.Message): The message object.

        Notes:
        - This example function will be called every time a message is sent in
        any channel.
        """
        # Avoid responding to your own messages
        if message.author == self.bot.user:
            return

        # Respond to a specific message content
        if message.content.lower() == 'ping':
            await message.channel.send('Pong!')


# Define the setup function that will be called when loading the cog
def setup(bot):
    bot.add_cog(CogTemplate(bot))
