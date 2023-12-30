"""
Discord Bot Event Handler Template

This example contains a template for creating new event handlers for Tux. It is designed to be have a 
familiar and straightforward command structure, with each event being able to have its own function.

Link to discord.py event reference:
https://discordpy.readthedocs.io/en/latest/api.html#event-reference

To use this template, replace `EventName` with the name of your event handler class. 
Replace `@commands.command` sections and their respective functions with the commands you
wish to create. Refer to the given 'hello' command as an example.

For each command, ensure that you have:
1. A name parameter that defines the command's call sign (i.e., the string that must be typed 
   out to call the command).
2. A help parameter that succinctly but clearly describes what the command does. This 
   description will be displayed in the bot's help command.
3. Refer to the given 'on_message' listener as an example for creating event listeners.
4. Remember to properly use the TuxLogger for outputting events to console and files. For 
   example:
    - logger.info("This is an information message.")
    - logger.warning("This is a warning message.")
    - logger.error("This is an error message.")
    - logger.debug("This is a debug message.")

After defining the event handler functions in the EventName class and the setup function,
replace this block comment with a description of what your particular event is meant to do.

Happy Coding!

P.S - For avoiding too long line linter errors, you can use the following syntax:
""" # noqa: E501

from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class EventName(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        An event listener that triggers when a message is sent.
        Parameters:
        - message (discord.Message): The message object.
        Notes:
        - This function will be called every time a message is sent in any channel.
        - Avoid responding to your own messages.
        """
        if message.author == self.bot.user:
            return

        if message.content.lower() == "ping":
            logger.debug("Ping message detected.")
            await message.channel.send("Pong!")
            logger.info("Pong message sent.")


# The setup function that'll be called when loading the cog
async def setup(bot):
    logger.debug("Setting up...")
    await bot.add_cog(EventName(bot))
    logger.info("Setup completed successfully.")
