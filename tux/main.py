import os
import discord
from discord.ext import commands
from cog_loader import CogLoader
from utils._tux_logger import TuxLogger
from dotenv import load_dotenv

logger = TuxLogger(__name__)
load_dotenv()


async def setup(bot: commands.Bot, debug: bool=False):
    """
    Set up the bot including loading cogs and other necessary setup tasks.
    """
    await CogLoader.setup(bot, debug)
    logger.debug("Event handler setup completed.")


async def main():
    bot_prefix = '!'
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix=bot_prefix, intents=intents)


    await setup(bot, debug=True)

    @bot.command(name='sync')
    @commands.has_permissions(administrator=True)
    async def sync(ctx: commands.Context):
        if ctx.guild:
            bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        logger.info(f'{ctx.author} synced the slash command tree.')

    @bot.command(name='clear')
    @commands.has_permissions(administrator=True)
    async def clear(ctx: commands.Context):
        bot.tree.clear_commands(guild=ctx.guild)
        if ctx.guild:
            bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        logger.info(f'{ctx.author} cleared the slash command tree.')

    @bot.event
    async def on_ready():
        logger.info(f'{bot.user} has connected to Discord!', __name__)

    await bot.start(os.getenv('TOKEN') or '', reconnect=True)


if __name__ == '__main__':
    import asyncio

    # Run the main function
    asyncio.run(main())