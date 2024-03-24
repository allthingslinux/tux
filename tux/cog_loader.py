# tux/cog_loader.py
import logging
import os
import traceback

from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class CogLoader(commands.Cog):
    def __init__(self, bot: commands.Bot, debug: bool = False):
        """
        Constructor for the CogLoader Cog.
        """
        self.bot = bot
        self.debug = debug
        self.ignore_cogs = []
        if debug:
            logger.setLevel(logging.DEBUG)

    def check_cog_eligibility(self, filename, cog_name):
        """
        Check if a cog module is eligible to be loaded.
        A cog module is eligible if it ends with '.py', it's not in the
        list of ignored cogs and doesn't start with an underscore.

        Args:
            filename: Name of the file.
            cog_name: Name of the cog.
        Returns:
            bool: True if the cog module is eligible, False otherwise.
        """

        return (
            filename.endswith(".py")
            and cog_name not in self.ignore_cogs
            and not filename.startswith("_")
        )

    async def load_cogs_from_folder(self, folder_name):
        """
        Dynamically loads all cogs from a folder.
        Each cog module should be a Python file in the specified directory.
        The file name (excluding extension) is considered the cog name.

        Args:
            folder_name (str): The name of the folder containing the cogs.
        """
        cog_dir = os.path.join(os.path.dirname(__file__), folder_name)

        for filename in os.listdir(cog_dir):
            cog_name = filename[:-3]
            module = f"{folder_name}.{cog_name}"

            if not self.check_cog_eligibility(filename, cog_name):
                logger.info(f"Skipping {module}.", __name__)
                continue

            try:
                await self.bot.load_extension(module)
                logger.debug(f"Successfully loaded cog: {module}", __name__)
            except Exception as e:
                logger.error(f"Failed to load cog {module}. Error: {e}", __name__)
                logger.error(traceback.format_exc())

    @classmethod
    async def setup(cls, bot, debug=False):
        """
        Sets up the CogLoader Cog and adds it to the bot.

        Args:
            bot (commands.Bot): The instance of the Discord bot.
            debug (bool): A flag indicating whether debug mode is enabled.
        """

        cog = cls(bot, debug)

        for folder in ["utils", "events", "commands"]:
            await cog.load_cogs_from_folder(folder)

        await bot.add_cog(cog)
