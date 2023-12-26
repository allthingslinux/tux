import discord
from discord.ext import commands
from cog_loader import CogLoader
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


async def setup(bot, debug=False):
    """
    Set up the bot including loading cogs and other necessary setup tasks.

    Parameters:
        bot (commands.Bot): The instance of the Discord bot.
        debug (bool): A flag indicating whether debug mode is enabled.
    """
    logger.debug("Setting up event handler...")
    loader = CogLoader(bot, debug)
    await loader.setup(bot, debug)
    logger.debug("Event handler setup completed.")


async def main():
    bot_prefix = '!'
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

    # Set up the bot, including loading cogs
    await setup(bot, debug=True)

    @bot.event
    async def on_ready():
        """
        This function is called when the bot successfully connects to Discord.
        """
        logger.info(f'{bot.user} has connected to Discord!', __name__)

    # Start the bot
    await bot.start('MTE4MjE5NDU4NTY5OTYzMTEzNA.GUaYP5.qbUQSLvBYzZ6TsXP_P3Qx1RZiobPrCDgF3NWpQ', reconnect=True)


if __name__ == '__main__':
    import asyncio

    # Run the main function
    asyncio.run(main())
